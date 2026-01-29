from rest_framework import serializers
from .models import Doctor, Slot, Patient, Token, WaitingList


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'created_at']
        read_only_fields = ['id', 'created_at']


class SlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    available_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Slot
        fields = [
            'id', 'doctor', 'doctor_name', 'start_time', 'end_time',
            'max_capacity', 'current_capacity', 'available_capacity',
            'status', 'delay_minutes', 'created_at'
        ]
        read_only_fields = ['id', 'current_capacity', 'created_at']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class TokenSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    slot_info = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = [
            'id', 'slot', 'slot_info', 'patient', 'patient_name',
            'token_number', 'priority', 'category', 'status',
            'estimated_time', 'actual_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'token_number', 'priority', 'estimated_time', 'created_at', 'updated_at']

    def get_slot_info(self, obj):
        return {
            'doctor': obj.slot.doctor.name,
            'start_time': obj.slot.start_time,
            'end_time': obj.slot.end_time
        }


class TokenCreateSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    patient_id = serializers.UUIDField()
    category = serializers.ChoiceField(choices=Token.CATEGORY_CHOICES)


class EmergencyTokenSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    patient_id = serializers.UUIDField()


class SlotDelaySerializer(serializers.Serializer):
    delay_minutes = serializers.IntegerField(min_value=0)


class WaitingListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)

    class Meta:
        model = WaitingList
        fields = ['id', 'slot', 'patient', 'patient_name', 'category', 'priority', 'created_at']
        read_only_fields = ['id', 'priority', 'created_at']
