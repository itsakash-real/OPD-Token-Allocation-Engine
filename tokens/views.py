from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Doctor, Slot, Patient, Token, WaitingList
from .serializers import (
    DoctorSerializer, SlotSerializer, PatientSerializer,
    TokenSerializer, TokenCreateSerializer, EmergencyTokenSerializer,
    SlotDelaySerializer, WaitingListSerializer
)
from .services import TokenAllocationService


class DoctorViewSet(viewsets.ModelViewSet):
    """API endpoints for managing doctors"""
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class PatientViewSet(viewsets.ModelViewSet):
    """API endpoints for managing patients"""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer


class SlotViewSet(viewsets.ModelViewSet):
    """API endpoints for managing time slots"""
    queryset = Slot.objects.select_related('doctor').all()
    serializer_class = SlotSerializer

    @extend_schema(
        request=SlotDelaySerializer,
        responses={200: SlotSerializer}
    )
    @action(detail=True, methods=['put'])
    def delay(self, request, pk=None):
        """Mark a slot as delayed and update all token times"""
        slot = self.get_object()
        serializer = SlotDelaySerializer(data=request.data)
        
        if serializer.is_valid():
            delay_minutes = serializer.validated_data['delay_minutes']
            
            lock = TokenAllocationService.acquire_slot_lock(slot.id)
            try:
                with lock:
                    success, message = TokenAllocationService.delay_slot(slot.id, delay_minutes)
                    
                    if success:
                        slot.refresh_from_db()
                        return Response({
                            'message': message,
                            'slot': SlotSerializer(slot).data
                        })
                    else:
                        return Response(
                            {'error': message},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                return Response(
                    {'error': f'Failed to acquire lock: {str(e)}'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: TokenSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def tokens(self, request, pk=None):
        """Get all tokens for a specific slot"""
        slot = self.get_object()
        tokens = Token.objects.filter(slot=slot).select_related('patient').order_by('token_number')
        serializer = TokenSerializer(tokens, many=True)
        return Response(serializer.data)


class TokenViewSet(viewsets.ModelViewSet):
    """API endpoints for managing tokens"""
    queryset = Token.objects.select_related('slot', 'patient', 'slot__doctor').all()
    serializer_class = TokenSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return TokenCreateSerializer
        return TokenSerializer

    @extend_schema(
        request=TokenCreateSerializer,
        responses={201: TokenSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Request a new token with priority-based allocation"""
        serializer = TokenCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            slot_id = serializer.validated_data['slot_id']
            patient_id = serializer.validated_data['patient_id']
            category = serializer.validated_data['category']

            # Acquire lock for concurrency control
            lock = TokenAllocationService.acquire_slot_lock(slot_id)
            
            try:
                with lock:
                    token, error = TokenAllocationService.allocate_token(
                        slot_id, patient_id, category
                    )
                    
                    if token:
                        return Response(
                            TokenSerializer(token).data,
                            status=status.HTTP_201_CREATED
                        )
                    else:
                        return Response(
                            {'error': error},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                return Response(
                    {'error': f'Failed to acquire lock: {str(e)}'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}})
    def destroy(self, request, *args, **kwargs):
        """Cancel a token"""
        token = self.get_object()
        
        lock = TokenAllocationService.acquire_slot_lock(token.slot_id)
        try:
            with lock:
                success, message = TokenAllocationService.cancel_token(token.id)
                
                if success:
                    return Response({'message': message})
                else:
                    return Response(
                        {'error': message},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            return Response(
                {'error': f'Failed to acquire lock: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @extend_schema(
        request=EmergencyTokenSerializer,
        responses={201: TokenSerializer}
    )
    @action(detail=False, methods=['post'])
    def emergency(self, request):
        """Insert an emergency patient at position 1"""
        serializer = EmergencyTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            slot_id = serializer.validated_data['slot_id']
            patient_id = serializer.validated_data['patient_id']

            lock = TokenAllocationService.acquire_slot_lock(slot_id)
            try:
                with lock:
                    token, error = TokenAllocationService.insert_emergency(slot_id, patient_id)
                    
                    if token:
                        # Get affected tokens
                        affected_tokens = Token.objects.filter(
                            slot_id=slot_id,
                            status='CONFIRMED',
                            token_number__gt=1
                        ).order_by('token_number')
                        
                        return Response({
                            'token': TokenSerializer(token).data,
                            'affected_tokens': TokenSerializer(affected_tokens, many=True).data,
                            'message': 'Emergency patient inserted at position 1'
                        }, status=status.HTTP_201_CREATED)
                    else:
                        return Response(
                            {'error': error},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                return Response(
                    {'error': f'Failed to acquire lock: {str(e)}'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}})
    @action(detail=True, methods=['post'])
    def no_show(self, request, pk=None):
        """Mark a token as no-show"""
        token = self.get_object()
        
        lock = TokenAllocationService.acquire_slot_lock(token.slot_id)
        try:
            with lock:
                success, message = TokenAllocationService.mark_no_show(token.id)
                
                if success:
                    return Response({'message': message})
                else:
                    return Response(
                        {'error': message},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            return Response(
                {'error': f'Failed to acquire lock: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ReportViewSet(viewsets.ViewSet):
    """API endpoints for reports and analytics"""

    @extend_schema(
        parameters=[
            OpenApiParameter('date', required=False, type=str, description='Report date (YYYY-MM-DD)'),
            OpenApiParameter('doctor_id', required=False, type=str, description='Filter by doctor UUID'),
        ]
    )
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Generate daily allocation report"""
        # Get date parameter or use today
        date_str = request.query_params.get('date')
        if date_str:
            report_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = timezone.now().date()

        # Build filters
        slot_filter = Q(start_time__date=report_date)
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            slot_filter &= Q(doctor_id=doctor_id)

        # Get slots for the day
        slots = Slot.objects.filter(slot_filter)
        total_slots = slots.count()

        # Get tokens for these slots
        tokens = Token.objects.filter(slot__in=slots)
        
        # Category breakdown
        category_stats = tokens.values('category').annotate(count=Count('id'))
        
        # Status breakdown
        status_stats = tokens.values('status').annotate(count=Count('id'))
        
        # Calculate rates
        total_tokens = tokens.count()
        confirmed = tokens.filter(status='CONFIRMED').count()
        cancelled = tokens.filter(status='CANCELLED').count()
        no_shows = tokens.filter(status='NO_SHOW').count()
        completed = tokens.filter(status='COMPLETED').count()

        # Capacity utilization
        total_capacity = sum(slot.max_capacity for slot in slots)
        utilization = (confirmed / total_capacity * 100) if total_capacity > 0 else 0

        report = {
            'date': report_date,
            'total_slots': total_slots,
            'total_tokens': total_tokens,
            'confirmed_tokens': confirmed,
            'cancelled_tokens': cancelled,
            'no_show_tokens': no_shows,
            'completed_tokens': completed,
            'cancellation_rate': round((cancelled / total_tokens * 100) if total_tokens > 0 else 0, 2),
            'no_show_rate': round((no_shows / total_tokens * 100) if total_tokens > 0 else 0, 2),
            'capacity_utilization': round(utilization, 2),
            'category_breakdown': list(category_stats),
            'status_breakdown': list(status_stats),
        }

        return Response(report)


class WaitingListViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for viewing waiting list"""
    queryset = WaitingList.objects.select_related('slot', 'patient').all()
    serializer_class = WaitingListSerializer

    @action(detail=False, methods=['get'])
    def by_slot(self, request):
        """Get waiting list for a specific slot"""
        slot_id = request.query_params.get('slot_id')
        if not slot_id:
            return Response(
                {'error': 'slot_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        waiting_list = self.queryset.filter(slot_id=slot_id).order_by('priority', 'created_at')
        serializer = self.get_serializer(waiting_list, many=True)
        return Response(serializer.data)
