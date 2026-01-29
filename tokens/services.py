from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.core.cache import cache
from django.utils import timezone
from .models import Token, Slot, Patient, WaitingList


class TokenAllocationService:
    """Core service for token allocation with priority management"""

    # Priority values (lower = higher priority)
    PRIORITY_VALUES = {
        'EMERGENCY': 1,
        'PRIORITY_PAID': 2,
        'FOLLOWUP': 3,
        'ONLINE': 4,
        'WALKIN': 5,
    }

    AVG_CONSULTATION_TIME = 10  # minutes per patient

    @classmethod
    def calculate_priority(cls, category, booking_time=None):
        """
        Calculate final priority score
        Formula: Base Priority - Time Bonus
        Time Bonus: (hours since booking) × 0.1, capped at 1.0
        """
        base_priority = cls.PRIORITY_VALUES.get(category, 5)
        
        if booking_time is None:
            booking_time = timezone.now()
        
        # Calculate time bonus
        hours_since_booking = (timezone.now() - booking_time).total_seconds() / 3600
        time_bonus = min(hours_since_booking * 0.1, 1.0)
        
        final_priority = base_priority - time_bonus
        return round(final_priority, 2)

    @classmethod
    def calculate_estimated_time(cls, slot, token_number):
        """Calculate estimated appointment time based on position"""
        minutes_offset = (token_number - 1) * cls.AVG_CONSULTATION_TIME
        estimated_time = slot.start_time + timedelta(minutes=minutes_offset + slot.delay_minutes)
        return estimated_time

    @classmethod
    def acquire_slot_lock(cls, slot_id, timeout=10, blocking_timeout=5):
        """Acquire distributed lock for a slot"""
        lock_key = f"slot_lock:{slot_id}"
        return cache.lock(lock_key, timeout=timeout, blocking_timeout=blocking_timeout)

    @classmethod
    @transaction.atomic
    def allocate_token(cls, slot_id, patient_id, category):
        """
        Main token allocation method with concurrency handling
        Returns: (token, error_message)
        """
        try:
            slot = Slot.objects.select_for_update().get(id=slot_id, status='ACTIVE')
        except Slot.DoesNotExist:
            return None, "Slot not found or not active"

        # Check capacity
        if slot.current_capacity >= slot.max_capacity:
            # Add to waiting list
            cls._add_to_waiting_list(slot, patient_id, category)
            return None, "Slot is full. Added to waiting list."

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return None, "Patient not found"

        # Check for duplicate booking on same day
        slot_date = slot.start_time.date()
        existing_tokens = Token.objects.filter(
            patient=patient,
            status='CONFIRMED',
            slot__start_time__date=slot_date
        ).exists()
        
        if existing_tokens:
            return None, "Patient already has a booking for this day"

        # Calculate priority
        priority = cls.calculate_priority(category)

        # Find insertion position
        existing_tokens = list(Token.objects.filter(
            slot=slot,
            status='CONFIRMED'
        ).order_by('priority', 'token_number'))

        position = 1
        for token in existing_tokens:
            if priority < token.priority:
                break
            position += 1

        # Resequence existing tokens if needed
        if position <= len(existing_tokens):
            cls._resequence_tokens(slot, position)

        # Create new token
        token = Token.objects.create(
            slot=slot,
            patient=patient,
            token_number=position,
            priority=priority,
            category=category,
            status='CONFIRMED',
            estimated_time=cls.calculate_estimated_time(slot, position)
        )

        # Update slot capacity
        slot.current_capacity = F('current_capacity') + 1
        slot.save(update_fields=['current_capacity'])

        # Refresh to get updated capacity
        slot.refresh_from_db()

        return token, None

    @classmethod
    def _resequence_tokens(cls, slot, from_position):
        """Shift tokens after insertion point"""
        tokens_to_shift = Token.objects.filter(
            slot=slot,
            token_number__gte=from_position,
            status='CONFIRMED'
        ).order_by('token_number')

        for token in tokens_to_shift:
            token.token_number += 1
            token.estimated_time = cls.calculate_estimated_time(slot, token.token_number)
            token.save(update_fields=['token_number', 'estimated_time'])

    @classmethod
    def _add_to_waiting_list(cls, slot, patient_id, category):
        """Add patient to waiting list when slot is full"""
        try:
            patient = Patient.objects.get(id=patient_id)
            priority = cls.calculate_priority(category)
            
            WaitingList.objects.create(
                slot=slot,
                patient=patient,
                category=category,
                priority=priority
            )
        except Patient.DoesNotExist:
            pass

    @classmethod
    @transaction.atomic
    def cancel_token(cls, token_id):
        """Cancel a token and handle reallocation"""
        try:
            token = Token.objects.select_for_update().get(id=token_id)
        except Token.DoesNotExist:
            return False, "Token not found"

        if token.status != 'CONFIRMED':
            return False, "Token is not in confirmed status"

        slot = Slot.objects.select_for_update().get(id=token.slot_id)
        
        # Mark token as cancelled
        token.status = 'CANCELLED'
        token.save(update_fields=['status'])

        # Decrease capacity
        slot.current_capacity = F('current_capacity') - 1
        slot.save(update_fields=['current_capacity'])

        # Check waiting list
        waiting = WaitingList.objects.filter(slot=slot).order_by('priority', 'created_at').first()
        
        if waiting:
            # Promote waiting patient
            new_token, error = cls.allocate_token(slot.id, waiting.patient_id, waiting.category)
            if new_token:
                waiting.delete()
        else:
            # Compact tokens (remove gap)
            cls._compact_tokens(slot)

        return True, "Token cancelled successfully"

    @classmethod
    def _compact_tokens(cls, slot):
        """Remove gaps in token sequence after cancellation"""
        confirmed_tokens = Token.objects.filter(
            slot=slot,
            status='CONFIRMED'
        ).order_by('token_number')

        for idx, token in enumerate(confirmed_tokens, start=1):
            if token.token_number != idx:
                token.token_number = idx
                token.estimated_time = cls.calculate_estimated_time(slot, idx)
                token.save(update_fields=['token_number', 'estimated_time'])

    @classmethod
    @transaction.atomic
    def insert_emergency(cls, slot_id, patient_id):
        """Insert emergency patient at position 1"""
        try:
            slot = Slot.objects.select_for_update().get(id=slot_id, status='ACTIVE')
        except Slot.DoesNotExist:
            return None, "Slot not found or not active"

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return None, "Patient not found"

        # Emergency always gets priority 1
        priority = 1.0

        # Shift all existing tokens
        Token.objects.filter(slot=slot, status='CONFIRMED').update(
            token_number=F('token_number') + 1
        )

        # Recalculate estimated times for all tokens
        all_tokens = Token.objects.filter(slot=slot, status='CONFIRMED').order_by('token_number')
        for token in all_tokens:
            token.estimated_time = cls.calculate_estimated_time(slot, token.token_number)
            token.save(update_fields=['estimated_time'])

        # Create emergency token at position 1
        token = Token.objects.create(
            slot=slot,
            patient=patient,
            token_number=1,
            priority=priority,
            category='EMERGENCY',
            status='CONFIRMED',
            estimated_time=cls.calculate_estimated_time(slot, 1)
        )

        # Update capacity (allow emergency to exceed if needed)
        if slot.current_capacity < slot.max_capacity:
            slot.current_capacity = F('current_capacity') + 1
            slot.save(update_fields=['current_capacity'])

        return token, None

    @classmethod
    @transaction.atomic
    def mark_no_show(cls, token_id):
        """Mark token as no-show"""
        try:
            token = Token.objects.get(id=token_id)
        except Token.DoesNotExist:
            return False, "Token not found"

        token.status = 'NO_SHOW'
        token.save(update_fields=['status'])

        # Handle as cancellation after grace period
        # In production, this would be scheduled via Celery
        return cls.cancel_token(token_id)

    @classmethod
    @transaction.atomic
    def delay_slot(cls, slot_id, delay_minutes):
        """Add delay to slot and update all token times"""
        try:
            slot = Slot.objects.select_for_update().get(id=slot_id)
        except Slot.DoesNotExist:
            return False, "Slot not found"

        # Update slot delay
        slot.delay_minutes += delay_minutes
        slot.status = 'DELAYED'
        slot.save(update_fields=['delay_minutes', 'status'])

        # Update all token estimated times
        tokens = Token.objects.filter(slot=slot, status='CONFIRMED')
        for token in tokens:
            token.estimated_time = cls.calculate_estimated_time(slot, token.token_number)
            token.save(update_fields=['estimated_time'])

        return True, f"Slot delayed by {delay_minutes} minutes"
