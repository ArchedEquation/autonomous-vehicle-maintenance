"""
Scheduling Agent - Intelligent Appointment Optimization
Handles booking, optimization, load balancing, and emergency scheduling
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import random

try:
    from tensorflow import keras
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("TensorFlow not available - using rule-based scheduling")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduling_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SchedulingAgent')


class UrgencyLevel(Enum):
    """Urgency levels for scheduling priority"""
    EMERGENCY = 1      # Immediate, override normal rules
    CRITICAL = 2       # Within 24 hours
    URGENT = 3         # Within 48 hours
    HIGH = 4           # Within 1 week
    NORMAL = 5         # Within 2 weeks
    ROUTINE = 6        # Flexible scheduling


class AppointmentStatus(Enum):
    """Appointment status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class TechnicianExpertise(Enum):
    """Technician expertise levels"""
    MASTER = "master"           # All repairs
    SENIOR = "senior"           # Complex repairs
    INTERMEDIATE = "intermediate"  # Standard repairs
    JUNIOR = "junior"           # Basic maintenance


@dataclass
class ServiceCenter:
    """Service center information"""
    center_id: str
    name: str
    location: Dict[str, float]  # {'lat': float, 'lon': float}
    capacity: int  # Max appointments per day
    operating_hours: Dict[str, str]  # {'start': '08:00', 'end': '18:00'}
    technicians: List[Dict[str, Any]]  # List of technician info
    specializations: List[str]  # Types of services offered
    parts_inventory: Dict[str, int]  # Available parts
    current_load: float = 0.0  # Current workload (0-1)
    
    def has_expertise(self, required_expertise: str) -> bool:
        """Check if center has required expertise"""
        return any(
            tech['expertise'] in [TechnicianExpertise.MASTER.value, TechnicianExpertise.SENIOR.value]
            or required_expertise in tech.get('specializations', [])
            for tech in self.technicians
        )
    
    def has_parts(self, required_parts: List[str]) -> bool:
        """Check if center has required parts"""
        return all(
            part in self.parts_inventory and self.parts_inventory[part] > 0
            for part in required_parts
        )


@dataclass
class BookingRequest:
    """Booking request from Customer Engagement Agent"""
    request_id: str
    vehicle_id: str
    customer_id: str
    urgency_level: UrgencyLevel
    services_required: List[str]
    estimated_duration: float  # hours
    diagnostic_details: Dict[str, Any]
    customer_preferences: Dict[str, Any]
    parts_needed: List[str] = field(default_factory=list)
    required_expertise: Optional[str] = None
    preferred_date: Optional[datetime] = None
    preferred_time: Optional[str] = None  # morning, afternoon, evening
    preferred_center: Optional[str] = None
    customer_location: Optional[Dict[str, float]] = None


@dataclass
class TimeSlot:
    """Available time slot"""
    slot_id: str
    center_id: str
    start_time: datetime
    end_time: datetime
    technician_id: str
    technician_expertise: str
    available: bool = True
    reserved_for_emergency: bool = False


@dataclass
class Appointment:
    """Scheduled appointment"""
    appointment_id: str
    request_id: str
    vehicle_id: str
    customer_id: str
    center_id: str
    center_name: str
    slot: TimeSlot
    services: List[str]
    estimated_duration: float
    estimated_cost: float
    status: AppointmentStatus
    diagnostic_details: Dict[str, Any]
    technician_assigned: str
    parts_reserved: List[str]
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.confirmed_at:
            data['confirmed_at'] = self.confirmed_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class SchedulingResult:
    """Result of scheduling operation"""
    success: bool
    appointment: Optional[Appointment] = None
    alternatives: List[Appointment] = field(default_factory=list)
    reason: str = ""
    optimization_score: float = 0.0


class ServiceSchedulerAPI:
    """
    Mock Service Scheduler API
    In production, this would connect to actual service center systems
    """
    
    def __init__(self):
        self.service_centers: Dict[str, ServiceCenter] = {}
        self.appointments: Dict[str, Appointment] = {}
        self._initialize_service_centers()
        logger.info("Service Scheduler API initialized")
    
    def _initialize_service_centers(self):
        """Initialize mock service centers"""
        centers_data = [
            {
                'center_id': 'SC001',
                'name': 'Downtown Service Center',
                'location': {'lat': 40.7128, 'lon': -74.0060},
                'capacity': 20,
                'operating_hours': {'start': '07:00', 'end': '19:00'},
                'technicians': [
                    {'id': 'T001', 'name': 'John Smith', 'expertise': 'master', 'specializations': ['engine', 'transmission']},
                    {'id': 'T002', 'name': 'Jane Doe', 'expertise': 'senior', 'specializations': ['electrical', 'brakes']},
                    {'id': 'T003', 'name': 'Bob Johnson', 'expertise': 'intermediate', 'specializations': ['maintenance']},
                ],
                'specializations': ['engine', 'transmission', 'electrical', 'brakes', 'maintenance'],
                'parts_inventory': {'brake_pads': 50, 'oil_filter': 100, 'battery': 20, 'thermostat': 15}
            },
            {
                'center_id': 'SC002',
                'name': 'North Branch',
                'location': {'lat': 40.7589, 'lon': -73.9851},
                'capacity': 15,
                'operating_hours': {'start': '08:00', 'end': '18:00'},
                'technicians': [
                    {'id': 'T004', 'name': 'Alice Brown', 'expertise': 'senior', 'specializations': ['engine', 'cooling']},
                    {'id': 'T005', 'name': 'Charlie Wilson', 'expertise': 'intermediate', 'specializations': ['maintenance', 'brakes']},
                ],
                'specializations': ['engine', 'cooling', 'maintenance', 'brakes'],
                'parts_inventory': {'brake_pads': 30, 'oil_filter': 80, 'coolant': 50, 'thermostat': 10}
            },
            {
                'center_id': 'SC003',
                'name': 'South Branch',
                'location': {'lat': 40.6782, 'lon': -73.9442},
                'capacity': 18,
                'operating_hours': {'start': '08:00', 'end': '20:00'},
                'technicians': [
                    {'id': 'T006', 'name': 'David Lee', 'expertise': 'master', 'specializations': ['engine', 'transmission', 'electrical']},
                    {'id': 'T007', 'name': 'Emma Davis', 'expertise': 'senior', 'specializations': ['brakes', 'suspension']},
                    {'id': 'T008', 'name': 'Frank Miller', 'expertise': 'junior', 'specializations': ['maintenance']},
                ],
                'specializations': ['engine', 'transmission', 'electrical', 'brakes', 'suspension', 'maintenance'],
                'parts_inventory': {'brake_pads': 40, 'oil_filter': 90, 'battery': 25, 'suspension_parts': 20}
            }
        ]
        
        for center_data in centers_data:
            center = ServiceCenter(**center_data)
            self.service_centers[center.center_id] = center
    
    def get_available_slots(
        self,
        center_id: str,
        start_date: datetime,
        end_date: datetime,
        duration: float
    ) -> List[TimeSlot]:
        """Get available time slots for a service center"""
        center = self.service_centers.get(center_id)
        if not center:
            return []
        
        slots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_date:
            # Parse operating hours
            start_hour = int(center.operating_hours['start'].split(':')[0])
            end_hour = int(center.operating_hours['end'].split(':')[0])
            
            # Generate slots for each technician
            for tech in center.technicians:
                current_time = current_date.replace(hour=start_hour)
                end_time = current_date.replace(hour=end_hour)
                
                while current_time + timedelta(hours=duration) <= end_time:
                    slot_id = f"{center_id}_{tech['id']}_{current_time.strftime('%Y%m%d%H%M')}"
                    
                    # Check if slot is already booked
                    is_available = not any(
                        apt.slot.slot_id == slot_id and apt.status == AppointmentStatus.CONFIRMED
                        for apt in self.appointments.values()
                    )
                    
                    if is_available:
                        slot = TimeSlot(
                            slot_id=slot_id,
                            center_id=center_id,
                            start_time=current_time,
                            end_time=current_time + timedelta(hours=duration),
                            technician_id=tech['id'],
                            technician_expertise=tech['expertise'],
                            available=True,
                            reserved_for_emergency=(current_time.hour == start_hour)  # First slot reserved
                        )
                        slots.append(slot)
                    
                    current_time += timedelta(hours=1)  # 1-hour intervals
            
            current_date += timedelta(days=1)
        
        return slots
    
    def book_appointment(self, appointment: Appointment) -> bool:
        """Book an appointment"""
        # Reserve parts
        center = self.service_centers[appointment.center_id]
        for part in appointment.parts_reserved:
            if part in center.parts_inventory:
                center.parts_inventory[part] -= 1
        
        # Store appointment
        self.appointments[appointment.appointment_id] = appointment
        
        # Update center load
        self._update_center_load(appointment.center_id)
        
        logger.info(f"Booked appointment {appointment.appointment_id} at {appointment.center_name}")
        return True
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment"""
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return False
        
        # Release parts
        center = self.service_centers[appointment.center_id]
        for part in appointment.parts_reserved:
            if part in center.parts_inventory:
                center.parts_inventory[part] += 1
        
        # Update status
        appointment.status = AppointmentStatus.CANCELLED
        
        # Update center load
        self._update_center_load(appointment.center_id)
        
        logger.info(f"Cancelled appointment {appointment_id}")
        return True
    
    def _update_center_load(self, center_id: str):
        """Update service center load"""
        center = self.service_centers[center_id]
        
        # Count confirmed appointments
        confirmed_count = sum(
            1 for apt in self.appointments.values()
            if apt.center_id == center_id and apt.status == AppointmentStatus.CONFIRMED
        )
        
        center.current_load = confirmed_count / center.capacity if center.capacity > 0 else 0


class SchedulingAgent:
    """
    Intelligent Scheduling Agent
    
    Features:
    - ML-based load prediction
    - Optimization algorithm for slot allocation
    - Multi-factor scheduling (location, urgency, expertise, parts)
    - Emergency slot handling
    - Load balancing across centers
    - Rescheduling and cancellation
    """
    
    def __init__(
        self,
        load_model_path: str = 'weights_and_metadata/service_load_lstm_model.weights.h5',
        scheduling_model_path: str = 'best_model.keras'
    ):
        """
        Initialize Scheduling Agent
        
        Args:
            load_model_path: Path to service center load prediction model
            scheduling_model_path: Path to appointment scheduling optimization model
        """
        self.load_model_path = load_model_path
        self.scheduling_model_path = scheduling_model_path
        
        # Load ML models
        self.load_model = None
        self.scheduling_model = None
        self._load_models()
        
        # Service Scheduler API
        self.scheduler_api = ServiceSchedulerAPI()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_bookings': 0,
            'emergency_bookings': 0,
            'rescheduled': 0,
            'cancelled': 0,
            'average_optimization_score': 0.0
        }
        
        # Optimization weights
        self.optimization_weights = {
            'urgency': 0.30,
            'customer_preference': 0.20,
            'distance': 0.15,
            'load_balance': 0.15,
            'expertise_match': 0.10,
            'parts_availability': 0.10
        }
        
        logger.info("Scheduling Agent initialized")
    
    def _load_models(self):
        """Load ML models for load prediction and scheduling optimization"""
        if TENSORFLOW_AVAILABLE:
            try:
                # Load service center load prediction model
                self.load_model = keras.models.load_model(self.load_model_path)
                logger.info(f"Loaded load prediction model from {self.load_model_path}")
            except Exception as e:
                logger.warning(f"Could not load load model: {e}")
                self.load_model = None
            
            try:
                # Load appointment scheduling optimization model
                self.scheduling_model = keras.models.load_model(self.scheduling_model_path)
                logger.info(f"Loaded scheduling model from {self.scheduling_model_path}")
            except Exception as e:
                logger.warning(f"Could not load scheduling model: {e}")
                self.scheduling_model = None
        else:
            logger.warning("TensorFlow not available - using rule-based scheduling")
    
    def schedule_appointment(self, booking_request: BookingRequest) -> SchedulingResult:
        """
        Main entry point: Schedule an appointment based on booking request
        
        Args:
            booking_request: Booking request from Customer Engagement Agent
            
        Returns:
            SchedulingResult: Scheduling outcome with appointment details
        """
        self.stats['total_requests'] += 1
        
        logger.info(f"Processing booking request {booking_request.request_id} "
                   f"for vehicle {booking_request.vehicle_id}")
        
        # Handle emergency requests with special logic
        if booking_request.urgency_level == UrgencyLevel.EMERGENCY:
            return self._handle_emergency_booking(booking_request)
        
        # Get available service centers
        eligible_centers = self._get_eligible_centers(booking_request)
        
        if not eligible_centers:
            return SchedulingResult(
                success=False,
                reason="No eligible service centers found with required expertise and parts"
            )
        
        # Predict load for each center
        center_loads = self._predict_center_loads(eligible_centers)
        
        # Get available slots
        all_slots = self._get_available_slots(
            eligible_centers,
            booking_request
        )
        
        if not all_slots:
            return SchedulingResult(
                success=False,
                reason="No available slots found in the requested timeframe"
            )
        
        # Optimize slot selection
        optimized_slots = self._optimize_slot_selection(
            all_slots,
            booking_request,
            center_loads
        )
        
        if not optimized_slots:
            return SchedulingResult(
                success=False,
                reason="Could not find optimal slot"
            )
        
        # Create appointment from best slot
        best_slot = optimized_slots[0]
        appointment = self._create_appointment(booking_request, best_slot)
        
        # Book appointment
        success = self.scheduler_api.book_appointment(appointment)
        
        if success:
            appointment.status = AppointmentStatus.CONFIRMED
            appointment.confirmed_at = datetime.now()
            self.stats['successful_bookings'] += 1
            
            # Send notifications
            self._send_notifications(appointment)
            
            # Create alternatives
            alternatives = [
                self._create_appointment(booking_request, slot)
                for slot in optimized_slots[1:4]  # Top 3 alternatives
            ]
            
            return SchedulingResult(
                success=True,
                appointment=appointment,
                alternatives=alternatives,
                optimization_score=best_slot.optimization_score if hasattr(best_slot, 'optimization_score') else 0.0
            )
        else:
            return SchedulingResult(
                success=False,
                reason="Failed to book appointment"
            )

    def _handle_emergency_booking(self, booking_request: BookingRequest) -> SchedulingResult:
        """
        Handle emergency bookings with override logic
        Emergency slots bypass normal scheduling rules
        """
        logger.warning(f"EMERGENCY booking request {booking_request.request_id}")
        self.stats['emergency_bookings'] += 1
        
        # Get all centers with required capabilities
        eligible_centers = self._get_eligible_centers(booking_request)
        
        if not eligible_centers:
            return SchedulingResult(
                success=False,
                reason="No service centers available for emergency"
            )
        
        # Find nearest center with emergency slot
        nearest_center = self._find_nearest_center(
            eligible_centers,
            booking_request.customer_location
        )
        
        # Get emergency slots (reserved first slots of the day)
        now = datetime.now()
        emergency_slots = self.scheduler_api.get_available_slots(
            nearest_center.center_id,
            now,
            now + timedelta(hours=4),  # Next 4 hours
            booking_request.estimated_duration
        )
        
        # Filter for emergency-reserved or override any slot
        if not emergency_slots:
            # Override: Take any available slot
            emergency_slots = self.scheduler_api.get_available_slots(
                nearest_center.center_id,
                now,
                now + timedelta(hours=2),
                booking_request.estimated_duration
            )
        
        if not emergency_slots:
            # Last resort: bump a non-urgent appointment
            bumped_slot = self._bump_non_urgent_appointment(nearest_center.center_id)
            if bumped_slot:
                emergency_slots = [bumped_slot]
        
        if not emergency_slots:
            return SchedulingResult(
                success=False,
                reason="No emergency slots available - all centers at capacity"
            )
        
        # Book first available emergency slot
        emergency_slot = emergency_slots[0]
        appointment = self._create_appointment(booking_request, emergency_slot)
        appointment.notes = "EMERGENCY APPOINTMENT - Priority Override"
        
        success = self.scheduler_api.book_appointment(appointment)
        
        if success:
            appointment.status = AppointmentStatus.CONFIRMED
            appointment.confirmed_at = datetime.now()
            
            # Send urgent notifications
            self._send_emergency_notifications(appointment)
            
            return SchedulingResult(
                success=True,
                appointment=appointment,
                reason="Emergency slot allocated",
                optimization_score=1.0
            )
        else:
            return SchedulingResult(
                success=False,
                reason="Failed to book emergency appointment"
            )
    
    def _bump_non_urgent_appointment(self, center_id: str) -> Optional[TimeSlot]:
        """Bump a non-urgent appointment to make room for emergency"""
        # Find non-urgent appointments in next 4 hours
        now = datetime.now()
        
        for apt_id, apt in self.scheduler_api.appointments.items():
            if (apt.center_id == center_id and
                apt.status == AppointmentStatus.CONFIRMED and
                apt.slot.start_time > now and
                apt.slot.start_time < now + timedelta(hours=4)):
                
                # Check if appointment is non-urgent
                if 'urgency' in apt.diagnostic_details:
                    urgency = apt.diagnostic_details['urgency']
                    if urgency in ['routine', 'normal']:
                        # Reschedule this appointment
                        logger.warning(f"Bumping appointment {apt_id} for emergency")
                        self.reschedule_appointment(apt_id, reason="Emergency override")
                        return apt.slot
        
        return None
    
    def _get_eligible_centers(self, booking_request: BookingRequest) -> List[ServiceCenter]:
        """Get service centers that can handle the request"""
        eligible = []
        
        for center in self.scheduler_api.service_centers.values():
            # Check expertise
            if booking_request.required_expertise:
                if not center.has_expertise(booking_request.required_expertise):
                    continue
            
            # Check parts availability
            if booking_request.parts_needed:
                if not center.has_parts(booking_request.parts_needed):
                    continue
            
            # Check if services are offered
            if not any(service in center.specializations for service in booking_request.services_required):
                continue
            
            eligible.append(center)
        
        return eligible
    
    def _predict_center_loads(self, centers: List[ServiceCenter]) -> Dict[str, float]:
        """
        Predict future load for service centers using ML model
        
        Returns:
            Dict mapping center_id to predicted load (0-1)
        """
        loads = {}
        
        if self.load_model:
            try:
                for center in centers:
                    # Prepare features for load prediction
                    # In production, this would use historical data
                    features = self._prepare_load_features(center)
                    
                    # Predict load
                    predicted_load = self.load_model.predict(features, verbose=0)
                    loads[center.center_id] = float(predicted_load[0][0])
                    
                    logger.debug(f"Predicted load for {center.name}: {loads[center.center_id]:.2f}")
            except Exception as e:
                logger.error(f"Error predicting loads: {e}")
                # Fallback to current load
                loads = {center.center_id: center.current_load for center in centers}
        else:
            # Fallback: use current load
            loads = {center.center_id: center.current_load for center in centers}
        
        return loads
    
    def _prepare_load_features(self, center: ServiceCenter) -> np.ndarray:
        """Prepare features for load prediction model"""
        # Mock feature preparation
        # In production, this would include:
        # - Historical load patterns
        # - Day of week
        # - Time of day
        # - Seasonal factors
        # - Current appointments
        
        now = datetime.now()
        features = [
            center.current_load,
            now.weekday(),  # 0-6
            now.hour,  # 0-23
            len(center.technicians),
            center.capacity
        ]
        
        # Reshape for LSTM: (samples, timesteps, features)
        return np.array([features] * 10).reshape(1, 10, len(features))
    
    def _get_available_slots(
        self,
        centers: List[ServiceCenter],
        booking_request: BookingRequest
    ) -> List[TimeSlot]:
        """Get available slots from eligible centers"""
        all_slots = []
        
        # Determine search window based on urgency
        now = datetime.now()
        if booking_request.urgency_level == UrgencyLevel.CRITICAL:
            end_date = now + timedelta(days=1)
        elif booking_request.urgency_level == UrgencyLevel.URGENT:
            end_date = now + timedelta(days=2)
        elif booking_request.urgency_level == UrgencyLevel.HIGH:
            end_date = now + timedelta(days=7)
        else:
            end_date = now + timedelta(days=14)
        
        # Override with preferred date if provided
        if booking_request.preferred_date:
            start_date = booking_request.preferred_date
            end_date = start_date + timedelta(days=3)
        else:
            start_date = now + timedelta(hours=2)  # Buffer time
        
        # Get slots from each center
        for center in centers:
            slots = self.scheduler_api.get_available_slots(
                center.center_id,
                start_date,
                end_date,
                booking_request.estimated_duration
            )
            all_slots.extend(slots)
        
        return all_slots
    
    def _optimize_slot_selection(
        self,
        slots: List[TimeSlot],
        booking_request: BookingRequest,
        center_loads: Dict[str, float]
    ) -> List[TimeSlot]:
        """
        Optimize slot selection using multi-factor scoring
        
        Factors:
        - Urgency match
        - Customer preference match
        - Distance to customer
        - Load balancing
        - Expertise match
        - Parts availability
        """
        scored_slots = []
        
        for slot in slots:
            score = self._calculate_slot_score(
                slot,
                booking_request,
                center_loads
            )
            
            # Attach score to slot for sorting
            slot.optimization_score = score
            scored_slots.append((score, slot))
        
        # Sort by score (descending)
        scored_slots.sort(key=lambda x: x[0], reverse=True)
        
        # Return sorted slots
        return [slot for score, slot in scored_slots]
    
    def _calculate_slot_score(
        self,
        slot: TimeSlot,
        booking_request: BookingRequest,
        center_loads: Dict[str, float]
    ) -> float:
        """Calculate optimization score for a slot"""
        score = 0.0
        weights = self.optimization_weights
        
        center = self.scheduler_api.service_centers[slot.center_id]
        
        # 1. Urgency score (0-1)
        urgency_score = self._score_urgency_match(slot, booking_request)
        score += urgency_score * weights['urgency']
        
        # 2. Customer preference score (0-1)
        preference_score = self._score_customer_preference(slot, booking_request)
        score += preference_score * weights['customer_preference']
        
        # 3. Distance score (0-1)
        distance_score = self._score_distance(center, booking_request.customer_location)
        score += distance_score * weights['distance']
        
        # 4. Load balance score (0-1)
        load_score = 1.0 - center_loads.get(slot.center_id, 0.5)
        score += load_score * weights['load_balance']
        
        # 5. Expertise match score (0-1)
        expertise_score = self._score_expertise_match(slot, booking_request)
        score += expertise_score * weights['expertise_match']
        
        # 6. Parts availability score (0-1)
        parts_score = 1.0 if center.has_parts(booking_request.parts_needed) else 0.5
        score += parts_score * weights['parts_availability']
        
        return score
    
    def _score_urgency_match(self, slot: TimeSlot, booking_request: BookingRequest) -> float:
        """Score how well slot timing matches urgency"""
        time_until_slot = (slot.start_time - datetime.now()).total_seconds() / 3600  # hours
        
        if booking_request.urgency_level == UrgencyLevel.CRITICAL:
            # Want slot within 24 hours
            return max(0, 1.0 - (time_until_slot / 24))
        elif booking_request.urgency_level == UrgencyLevel.URGENT:
            # Want slot within 48 hours
            return max(0, 1.0 - (time_until_slot / 48))
        elif booking_request.urgency_level == UrgencyLevel.HIGH:
            # Want slot within 1 week
            return max(0, 1.0 - (time_until_slot / 168))
        else:
            # Flexible - prefer sooner but not critical
            return max(0, 0.5 + (1.0 - time_until_slot / 336) * 0.5)
    
    def _score_customer_preference(self, slot: TimeSlot, booking_request: BookingRequest) -> float:
        """Score match with customer preferences"""
        score = 0.5  # Base score
        
        # Preferred center
        if booking_request.preferred_center == slot.center_id:
            score += 0.3
        
        # Preferred time of day
        if booking_request.preferred_time:
            hour = slot.start_time.hour
            if booking_request.preferred_time == 'morning' and 7 <= hour < 12:
                score += 0.2
            elif booking_request.preferred_time == 'afternoon' and 12 <= hour < 17:
                score += 0.2
            elif booking_request.preferred_time == 'evening' and 17 <= hour < 21:
                score += 0.2
        
        return min(score, 1.0)
    
    def _score_distance(
        self,
        center: ServiceCenter,
        customer_location: Optional[Dict[str, float]]
    ) -> float:
        """Score based on distance to customer"""
        if not customer_location:
            return 0.5  # Neutral if no location
        
        # Calculate distance (simplified - use Haversine in production)
        distance = self._calculate_distance(
            customer_location,
            center.location
        )
        
        # Score: closer is better (within 50 miles)
        if distance < 5:
            return 1.0
        elif distance < 10:
            return 0.8
        elif distance < 20:
            return 0.6
        elif distance < 50:
            return 0.4
        else:
            return 0.2
    
    def _calculate_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """Calculate distance between two locations (simplified)"""
        # Simplified distance calculation
        # In production, use proper Haversine formula
        lat_diff = abs(loc1['lat'] - loc2['lat'])
        lon_diff = abs(loc1['lon'] - loc2['lon'])
        return ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 69  # Rough miles
    
    def _score_expertise_match(self, slot: TimeSlot, booking_request: BookingRequest) -> float:
        """Score technician expertise match"""
        if not booking_request.required_expertise:
            return 1.0  # No specific requirement
        
        expertise_levels = {
            'master': 1.0,
            'senior': 0.8,
            'intermediate': 0.6,
            'junior': 0.4
        }
        
        return expertise_levels.get(slot.technician_expertise, 0.5)
    
    def _find_nearest_center(
        self,
        centers: List[ServiceCenter],
        customer_location: Optional[Dict[str, float]]
    ) -> ServiceCenter:
        """Find nearest service center to customer"""
        if not customer_location:
            return centers[0]  # Return first if no location
        
        nearest = min(
            centers,
            key=lambda c: self._calculate_distance(customer_location, c.location)
        )
        
        return nearest
    
    def _create_appointment(
        self,
        booking_request: BookingRequest,
        slot: TimeSlot
    ) -> Appointment:
        """Create appointment from booking request and slot"""
        center = self.scheduler_api.service_centers[slot.center_id]
        
        # Estimate cost (simplified)
        base_cost = len(booking_request.services_required) * 100
        parts_cost = len(booking_request.parts_needed) * 50
        estimated_cost = base_cost + parts_cost
        
        appointment = Appointment(
            appointment_id=f"APT_{booking_request.request_id}_{slot.slot_id}",
            request_id=booking_request.request_id,
            vehicle_id=booking_request.vehicle_id,
            customer_id=booking_request.customer_id,
            center_id=slot.center_id,
            center_name=center.name,
            slot=slot,
            services=booking_request.services_required,
            estimated_duration=booking_request.estimated_duration,
            estimated_cost=estimated_cost,
            status=AppointmentStatus.PENDING,
            diagnostic_details=booking_request.diagnostic_details,
            technician_assigned=slot.technician_id,
            parts_reserved=booking_request.parts_needed,
            created_at=datetime.now()
        )
        
        return appointment
    
    def reschedule_appointment(
        self,
        appointment_id: str,
        new_preferred_date: Optional[datetime] = None,
        reason: str = ""
    ) -> SchedulingResult:
        """
        Reschedule an existing appointment
        
        Args:
            appointment_id: Appointment to reschedule
            new_preferred_date: New preferred date (optional)
            reason: Reason for rescheduling
            
        Returns:
            SchedulingResult: New appointment details
        """
        # Get existing appointment
        appointment = self.scheduler_api.appointments.get(appointment_id)
        if not appointment:
            return SchedulingResult(
                success=False,
                reason="Appointment not found"
            )
        
        # Cancel existing appointment
        self.scheduler_api.cancel_appointment(appointment_id)
        
        # Create new booking request from appointment
        booking_request = BookingRequest(
            request_id=f"RESCHEDULE_{appointment.request_id}",
            vehicle_id=appointment.vehicle_id,
            customer_id=appointment.customer_id,
            urgency_level=UrgencyLevel.NORMAL,  # Lower priority for reschedule
            services_required=appointment.services,
            estimated_duration=appointment.estimated_duration,
            diagnostic_details=appointment.diagnostic_details,
            parts_needed=appointment.parts_reserved,
            preferred_date=new_preferred_date,
            preferred_center=appointment.center_id
        )
        
        # Schedule new appointment
        result = self.schedule_appointment(booking_request)
        
        if result.success:
            result.appointment.notes = f"Rescheduled from {appointment_id}. Reason: {reason}"
            self.stats['rescheduled'] += 1
            logger.info(f"Rescheduled appointment {appointment_id}")
        
        return result
    
    def cancel_appointment(self, appointment_id: str, reason: str = "") -> bool:
        """
        Cancel an appointment
        
        Args:
            appointment_id: Appointment to cancel
            reason: Reason for cancellation
            
        Returns:
            bool: Success status
        """
        success = self.scheduler_api.cancel_appointment(appointment_id)
        
        if success:
            self.stats['cancelled'] += 1
            logger.info(f"Cancelled appointment {appointment_id}. Reason: {reason}")
        
        return success
    
    def _send_notifications(self, appointment: Appointment):
        """Send appointment notifications to customer and service center"""
        # Customer notification
        customer_notification = {
            'type': 'appointment_confirmed',
            'appointment_id': appointment.appointment_id,
            'customer_id': appointment.customer_id,
            'center_name': appointment.center_name,
            'date': appointment.slot.start_time.strftime('%Y-%m-%d'),
            'time': appointment.slot.start_time.strftime('%H:%M'),
            'services': appointment.services,
            'estimated_cost': appointment.estimated_cost,
            'estimated_duration': appointment.estimated_duration
        }
        logger.info(f"Customer notification: {json.dumps(customer_notification)}")
        
        # Service center notification
        center_notification = {
            'type': 'new_appointment',
            'appointment_id': appointment.appointment_id,
            'center_id': appointment.center_id,
            'vehicle_id': appointment.vehicle_id,
            'date': appointment.slot.start_time.strftime('%Y-%m-%d'),
            'time': appointment.slot.start_time.strftime('%H:%M'),
            'services': appointment.services,
            'diagnostic_details': appointment.diagnostic_details,
            'technician_assigned': appointment.technician_assigned,
            'parts_needed': appointment.parts_reserved,
            'estimated_duration': appointment.estimated_duration
        }
        logger.info(f"Service center notification: {json.dumps(center_notification)}")
    
    def _send_emergency_notifications(self, appointment: Appointment):
        """Send urgent notifications for emergency appointments"""
        # Urgent customer notification
        logger.warning(f"URGENT: Emergency appointment {appointment.appointment_id} "
                      f"scheduled for {appointment.slot.start_time}")
        
        # Alert service center
        logger.warning(f"URGENT: Service center {appointment.center_name} "
                      f"has emergency appointment at {appointment.slot.start_time}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduling agent statistics"""
        if self.stats['total_requests'] > 0:
            self.stats['success_rate'] = self.stats['successful_bookings'] / self.stats['total_requests']
        
        return self.stats
    
    def get_center_status(self, center_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a service center"""
        center = self.scheduler_api.service_centers.get(center_id)
        if not center:
            return None
        
        # Count appointments
        upcoming_appointments = [
            apt for apt in self.scheduler_api.appointments.values()
            if apt.center_id == center_id and 
            apt.status == AppointmentStatus.CONFIRMED and
            apt.slot.start_time > datetime.now()
        ]
        
        return {
            'center_id': center.center_id,
            'name': center.name,
            'current_load': center.current_load,
            'capacity': center.capacity,
            'upcoming_appointments': len(upcoming_appointments),
            'available_technicians': len(center.technicians),
            'parts_inventory': center.parts_inventory
        }


# Integration with Master Orchestrator
def create_scheduling_handler(agent: SchedulingAgent):
    """
    Create handler function for Master Orchestrator integration
    
    Args:
        agent: SchedulingAgent instance
        
    Returns:
        Handler function compatible with orchestrator
    """
    def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler for Master Orchestrator
        
        Args:
            payload: Contains customer engagement results
            
        Returns:
            Scheduling results dictionary
        """
        # Extract data from payload
        vehicle_id = payload['vehicle_id']
        customer_id = payload.get('customer_id', f'CUST_{vehicle_id}')
        diagnosis = payload.get('diagnosis_results', {})
        customer_prefs = payload.get('customer_preferences', {})
        urgency_score = payload.get('urgency_score', 0.5)
        
        # Determine urgency level
        if urgency_score > 0.9:
            urgency = UrgencyLevel.EMERGENCY
        elif urgency_score > 0.7:
            urgency = UrgencyLevel.CRITICAL
        elif urgency_score > 0.5:
            urgency = UrgencyLevel.URGENT
        elif urgency_score > 0.3:
            urgency = UrgencyLevel.HIGH
        else:
            urgency = UrgencyLevel.NORMAL
        
        # Create booking request
        booking_request = BookingRequest(
            request_id=f"REQ_{vehicle_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            urgency_level=urgency,
            services_required=diagnosis.get('recommended_services', ['inspection']),
            estimated_duration=diagnosis.get('estimated_duration', 2.0),
            diagnostic_details=diagnosis,
            parts_needed=diagnosis.get('parts_needed', []),
            required_expertise=diagnosis.get('required_expertise'),
            preferred_time=customer_prefs.get('preferred_time', 'morning'),
            preferred_center=customer_prefs.get('preferred_location')
        )
        
        # Schedule appointment
        result = agent.schedule_appointment(booking_request)
        
        # Convert to dict for orchestrator
        return {
            'success': result.success,
            'appointment': result.appointment.to_dict() if result.appointment else None,
            'alternatives': [apt.to_dict() for apt in result.alternatives],
            'reason': result.reason,
            'optimization_score': result.optimization_score
        }
    
    return handler


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print(" SCHEDULING AGENT - DEMONSTRATION")
    print("="*70)
    print()
    
    # Initialize agent
    agent = SchedulingAgent()
    
    # Test Scenario 1: Emergency Booking
    print("\n" + "="*70)
    print(" SCENARIO 1: EMERGENCY BOOKING")
    print("="*70 + "\n")
    
    emergency_request = BookingRequest(
        request_id="REQ001",
        vehicle_id="VEH001",
        customer_id="CUST001",
        urgency_level=UrgencyLevel.EMERGENCY,
        services_required=['engine_repair', 'cooling_system'],
        estimated_duration=3.0,
        diagnostic_details={
            'issue': 'engine overheating',
            'severity': 'critical',
            'safety_risk': True
        },
        customer_preferences={'preferred_time': 'morning'},
        parts_needed=['thermostat', 'coolant'],
        required_expertise='engine',
        customer_location={'lat': 40.7128, 'lon': -74.0060}
    )
    
    result1 = agent.schedule_appointment(emergency_request)
    
    print(f"Success: {result1.success}")
    if result1.appointment:
        print(f"Appointment ID: {result1.appointment.appointment_id}")
        print(f"Center: {result1.appointment.center_name}")
        print(f"Time: {result1.appointment.slot.start_time}")
        print(f"Technician: {result1.appointment.technician_assigned}")
        print(f"Status: {result1.appointment.status.value}")
        print(f"Notes: {result1.appointment.notes}")
    
    # Test Scenario 2: Normal Booking with Optimization
    print("\n\n" + "="*70)
    print(" SCENARIO 2: NORMAL BOOKING WITH OPTIMIZATION")
    print("="*70 + "\n")
    
    normal_request = BookingRequest(
        request_id="REQ002",
        vehicle_id="VEH002",
        customer_id="CUST002",
        urgency_level=UrgencyLevel.NORMAL,
        services_required=['oil_change', 'tire_rotation'],
        estimated_duration=1.5,
        diagnostic_details={
            'issue': 'routine_maintenance',
            'severity': 'low'
        },
        customer_preferences={'preferred_time': 'afternoon'},
        parts_needed=['oil_filter'],
        customer_location={'lat': 40.7589, 'lon': -73.9851}
    )
    
    result2 = agent.schedule_appointment(normal_request)
    
    print(f"Success: {result2.success}")
    if result2.appointment:
        print(f"Appointment ID: {result2.appointment.appointment_id}")
        print(f"Center: {result2.appointment.center_name}")
        print(f"Time: {result2.appointment.slot.start_time}")
        print(f"Optimization Score: {result2.optimization_score:.3f}")
        print(f"\nAlternatives: {len(result2.alternatives)}")
        for i, alt in enumerate(result2.alternatives[:2], 1):
            print(f"  {i}. {alt.center_name} at {alt.slot.start_time}")
    
    # Statistics
    print("\n\n" + "="*70)
    print(" AGENT STATISTICS")
    print("="*70 + "\n")
    
    stats = agent.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Service Center Status
    print("\n\n" + "="*70)
    print(" SERVICE CENTER STATUS")
    print("="*70 + "\n")
    
    for center_id in ['SC001', 'SC002', 'SC003']:
        status = agent.get_center_status(center_id)
        if status:
            print(f"\n{status['name']}:")
            print(f"  Load: {status['current_load']:.1%}")
            print(f"  Capacity: {status['capacity']}")
            print(f"  Upcoming: {status['upcoming_appointments']} appointments")
    
    print("\n" + "="*70)
    print(" Demonstration Complete!")
    print("="*70 + "\n")
