"""
Customer Engagement Agent - Voice/Chat Capable
Handles customer communication with sentiment analysis and response prediction
"""

import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Transformers not available - using rule-based fallback")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('customer_engagement_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CustomerEngagementAgent')


class UrgencyLevel(Enum):
    """Urgency levels for communication"""
    CRITICAL = "critical"
    URGENT = "urgent"
    PREVENTIVE = "preventive"
    ROUTINE = "routine"


class CommunicationChannel(Enum):
    """Communication channels"""
    PHONE_CALL = "phone_call"
    SMS = "sms"
    EMAIL = "email"
    APP_NOTIFICATION = "app_notification"
    CHAT = "chat"


class CustomerResponse(Enum):
    """Predicted customer responses"""
    ACCEPT = "accept"
    DECLINE = "decline"
    RESCHEDULE = "reschedule"
    NEED_INFO = "need_info"
    FRUSTRATED = "frustrated"
    UNCERTAIN = "uncertain"


class ConversationState(Enum):
    """Conversation states"""
    GREETING = "greeting"
    ISSUE_EXPLANATION = "issue_explanation"
    SCHEDULING = "scheduling"
    PREFERENCE_GATHERING = "preference_gathering"
    OBJECTION_HANDLING = "objection_handling"
    CONFIRMATION = "confirmation"
    ESCALATION = "escalation"
    COMPLETED = "completed"


@dataclass
class DiagnosticReport:
    """Diagnostic report from Master Agent"""
    vehicle_id: str
    customer_id: str
    urgency_level: UrgencyLevel
    issues_detected: List[str]
    recommended_services: List[str]
    estimated_cost: float
    risk_description: str
    time_to_failure_days: Optional[int] = None
    safety_critical: bool = False


@dataclass
class CustomerProfile:
    """Customer profile information"""
    customer_id: str
    name: str
    phone: str
    email: str
    preferred_channel: CommunicationChannel
    preferred_time: str  # morning, afternoon, evening
    preferred_location: Optional[str] = None
    language: str = "en"
    communication_style: str = "formal"  # formal, casual, technical
    previous_interactions: List[Dict[str, Any]] = None
    sentiment_history: List[float] = None
    
    def __post_init__(self):
        if self.previous_interactions is None:
            self.previous_interactions = []
        if self.sentiment_history is None:
            self.sentiment_history = []


@dataclass
class ConversationContext:
    """Maintains conversation context"""
    conversation_id: str
    customer_profile: CustomerProfile
    diagnostic_report: DiagnosticReport
    state: ConversationState
    messages: List[Dict[str, str]]
    customer_sentiment: float  # -1 to 1
    confidence_score: float  # 0 to 1
    objections_count: int = 0
    escalation_triggered: bool = False
    preferences_captured: Dict[str, Any] = None
    predicted_response: Optional[CustomerResponse] = None
    
    def __post_init__(self):
        if self.preferences_captured is None:
            self.preferences_captured = {}


@dataclass
class EngagementResult:
    """Result of customer engagement"""
    conversation_id: str
    customer_id: str
    vehicle_id: str
    outcome: CustomerResponse
    appointment_scheduled: bool
    appointment_details: Optional[Dict[str, Any]] = None
    customer_preferences: Dict[str, Any] = None
    sentiment_score: float = 0.0
    escalated_to_human: bool = False
    conversation_transcript: List[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['outcome'] = self.outcome.value
        return data


class CustomerEngagementAgent:
    """
    Customer Engagement Agent with Voice/Chat Capabilities
    
    Features:
    - Sentiment analysis
    - Response prediction
    - Natural dialogue generation
    - Objection handling
    - Preference capture
    - Escalation logic
    - Multi-channel support
    """
    
    def __init__(
        self,
        sentiment_model_path: str = 'sentiment_model_weights',
        confidence_threshold: float = 0.7,
        escalation_sentiment_threshold: float = -0.5
    ):
        """
        Initialize Customer Engagement Agent
        
        Args:
            sentiment_model_path: Path to sentiment analysis model
            confidence_threshold: Minimum confidence for autonomous operation
            escalation_sentiment_threshold: Sentiment below which to escalate
        """
        self.sentiment_model_path = sentiment_model_path
        self.confidence_threshold = confidence_threshold
        self.escalation_sentiment_threshold = escalation_sentiment_threshold
        
        # Load models
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self._load_models()
        
        # Conversation contexts
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Statistics
        self.stats = {
            'total_engagements': 0,
            'successful_schedules': 0,
            'escalations': 0,
            'declined': 0,
            'average_sentiment': 0.0
        }
        
        # Dialogue templates
        self._initialize_dialogue_templates()
        
        # Objection handlers
        self._initialize_objection_handlers()
        
        logger.info("Customer Engagement Agent initialized")
    
    def _load_models(self):
        """Load sentiment analysis and response prediction models"""
        if TRANSFORMERS_AVAILABLE:
            try:
                self.sentiment_tokenizer = AutoTokenizer.from_pretrained(
                    self.sentiment_model_path + '/tokenizer'
                )
                self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                    self.sentiment_model_path + '/full_model'
                )
                self.sentiment_model.eval()
                logger.info("Loaded sentiment analysis model")
            except Exception as e:
                logger.warning(f"Could not load sentiment model: {e}")
                self.sentiment_model = None
        else:
            logger.warning("Transformers not available - using rule-based sentiment")
    
    def _initialize_dialogue_templates(self):
        """Initialize dialogue templates for different scenarios"""
        self.dialogue_templates = {
            'greeting': {
                'formal': [
                    "Good {time_of_day}, {name}. This is {agent_name} from {company}. How are you today?",
                    "Hello {name}, this is {agent_name} calling from {company}. I hope I'm not catching you at a bad time.",
                ],
                'casual': [
                    "Hi {name}! This is {agent_name} from {company}. How's your day going?",
                    "Hey {name}, {agent_name} here from {company}. Got a minute to chat?",
                ]
            },
            'critical_issue': {
                'formal': [
                    "I'm calling because our diagnostic system has detected a critical issue with your {vehicle}. {issue_description}. For your safety, we strongly recommend immediate service. Can we schedule an appointment for you today?",
                    "{name}, I need to inform you about an urgent matter regarding your {vehicle}. We've identified {issue_description}. This is a safety concern that requires immediate attention. When would be the earliest you could bring your vehicle in?",
                ],
                'casual': [
                    "{name}, I've got some important news about your {vehicle}. Our system flagged {issue_description}. This is pretty serious and we really need to get you in today if possible. Can you make it?",
                    "Hey {name}, I need to talk to you about your {vehicle}. We found {issue_description} and it's something we need to address right away for your safety. What does your schedule look like today?",
                ]
            },
            'urgent_issue': {
                'formal': [
                    "Our diagnostic analysis indicates your {vehicle} has {issue_description}. While not immediately critical, this issue could lead to a breakdown within the next few days. We'd like to schedule service within 48 hours. Would {suggested_time} work for you?",
                    "{name}, we've detected {issue_description} in your {vehicle}. To prevent potential failure, we recommend scheduling service soon. Are you available this week?",
                ],
                'casual': [
                    "So, your {vehicle} is showing {issue_description}. It's not an emergency, but we should probably get it looked at in the next day or two. How's your schedule this week?",
                    "{name}, heads up - your {vehicle} has {issue_description}. Not critical yet, but let's get it fixed before it becomes a problem. Can you come in this week?",
                ]
            },
            'preventive': {
                'formal': [
                    "Good news - we're being proactive! Our analysis suggests your {vehicle} would benefit from preventive maintenance to avoid potential issues. Specifically, {issue_description}. Would you like to schedule service in the next couple of weeks?",
                    "{name}, based on your vehicle's data, we recommend preventive service for {issue_description}. This will help avoid future problems and keep your {vehicle} running smoothly. When would be convenient for you?",
                ],
                'casual': [
                    "Hey {name}, just being proactive here. Your {vehicle} could use some preventive care - {issue_description}. Better safe than sorry, right? Want to set something up?",
                    "Quick heads up, {name}. Your {vehicle} is due for some preventive maintenance. We're seeing {issue_description}. Let's get ahead of any problems. What works for you?",
                ]
            },
            'routine': {
                'formal': [
                    "Hello {name}, this is a courtesy reminder that your {vehicle} is due for scheduled maintenance. It's been {time_since_last} since your last service. Would you like to schedule an appointment?",
                    "{name}, your {vehicle} is ready for its routine service. We recommend scheduling within the next few weeks. What's your availability like?",
                ],
                'casual': [
                    "Hi {name}! Time for your {vehicle}'s regular checkup. It's been {time_since_last}. Want to get that scheduled?",
                    "Hey {name}, just a friendly reminder - your {vehicle} is due for service. Let's get you on the calendar!",
                ]
            },
            'cost_objection': [
                "I understand cost is a concern. Let me break down what we're looking at: {cost_breakdown}. Keep in mind, addressing this now will likely save you money compared to waiting for a more serious failure.",
                "That's a fair question. The estimated cost is {cost}, which includes {services}. We also offer payment plans if that would help. Would you like to hear about those options?",
                "I hear you. Here's the thing - this repair costs {cost} now, but if we wait and it fails completely, you could be looking at {higher_cost} plus towing. It's really about preventing a bigger expense.",
            ],
            'time_objection': [
                "I completely understand you're busy. The service will take approximately {duration} hours. We also offer loaner vehicles so you don't have to wait. Would that work better for you?",
                "Time is valuable, I get it. We have early morning and evening slots available. We can also pick up your vehicle and drop it off when done. Would either of those options help?",
                "I know it's inconvenient. What if we could get you in and out in {duration} hours? We'll prioritize your service. Does that sound more manageable?",
            ],
            'trust_objection': [
                "I appreciate your caution. Our diagnostic system uses advanced AI and has been validated by certified technicians. We're happy to show you the diagnostic data and have a technician explain everything. Would that help?",
                "That's a smart question. We're not just trying to sell you service - our system detected actual issues with your vehicle's sensors. We can send you the detailed report. Would you like to see it?",
                "I understand the skepticism. How about this - come in for a free inspection and we'll show you exactly what we found. No obligation. Fair enough?",
            ],
            'confirmation': [
                "Perfect! I've scheduled your appointment for {date} at {time} at our {location} service center. You'll receive a confirmation via {channel}. Is there anything else I can help you with?",
                "Great! You're all set for {date} at {time}. We'll send you a reminder 24 hours before. Looking forward to seeing you then!",
                "Excellent! Your appointment is confirmed: {date} at {time}, {location}. We'll take good care of your {vehicle}. See you then!",
            ],
            'escalation': [
                "I want to make sure you get the best service possible. Let me connect you with one of our senior service advisors who can address your concerns more thoroughly. One moment please.",
                "I appreciate your patience. To better assist you, I'd like to transfer you to a specialist who can provide more detailed information. Is that okay?",
            ]
        }
    
    def _initialize_objection_handlers(self):
        """Initialize objection handling strategies"""
        self.objection_patterns = {
            'cost': [
                r'too expensive', r'cost', r'afford', r'money', r'price',
                r'budget', r'cheaper', r'discount'
            ],
            'time': [
                r'busy', r'no time', r'schedule', r'later', r'wait',
                r'convenient', r'rush', r'hurry'
            ],
            'trust': [
                r'sure', r'really need', r'necessary', r'scam', r'trust',
                r'second opinion', r'verify', r'prove'
            ],
            'decline': [
                r'not interested', r'no thanks', r'don\'t want', r'cancel',
                r'stop calling', r'remove', r'unsubscribe'
            ]
        }
    
    def engage_customer(
        self,
        diagnostic_report: DiagnosticReport,
        customer_profile: CustomerProfile
    ) -> EngagementResult:
        """
        Main entry point: Engage customer based on diagnostic report
        
        Args:
            diagnostic_report: Diagnostic information
            customer_profile: Customer information
            
        Returns:
            EngagementResult: Outcome of engagement
        """
        # Create conversation context
        conversation_id = f"CONV_{diagnostic_report.vehicle_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        context = ConversationContext(
            conversation_id=conversation_id,
            customer_profile=customer_profile,
            diagnostic_report=diagnostic_report,
            state=ConversationState.GREETING,
            messages=[],
            customer_sentiment=0.0,
            confidence_score=1.0
        )
        
        self.active_conversations[conversation_id] = context
        self.stats['total_engagements'] += 1
        
        logger.info(f"Starting engagement {conversation_id} for customer {customer_profile.customer_id}")
        
        # Determine communication channel
        channel = self._select_channel(diagnostic_report.urgency_level, customer_profile)
        
        # Start conversation
        self._add_message(context, 'system', f"Channel: {channel.value}")
        
        # Greeting
        greeting = self._generate_greeting(context)
        self._add_message(context, 'agent', greeting)
        
        # Simulate customer response (in production, this would be actual customer input)
        customer_response = self._simulate_customer_response(context, "greeting")
        self._add_message(context, 'customer', customer_response)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(customer_response)
        context.customer_sentiment = sentiment
        
        # Explain issue
        context.state = ConversationState.ISSUE_EXPLANATION
        issue_explanation = self._generate_issue_explanation(context)
        self._add_message(context, 'agent', issue_explanation)
        
        # Simulate customer response
        customer_response = self._simulate_customer_response(context, "issue_explanation")
        self._add_message(context, 'customer', customer_response)
        
        # Predict response
        predicted_response = self._predict_customer_response(customer_response, context)
        context.predicted_response = predicted_response
        
        # Update sentiment
        sentiment = self._analyze_sentiment(customer_response)
        context.customer_sentiment = (context.customer_sentiment + sentiment) / 2
        
        # Check for escalation
        if self._should_escalate(context):
            return self._escalate_to_human(context)
        
        # Handle response
        if predicted_response == CustomerResponse.ACCEPT:
            return self._handle_acceptance(context)
        elif predicted_response in [CustomerResponse.DECLINE, CustomerResponse.FRUSTRATED]:
            return self._handle_decline(context)
        elif predicted_response == CustomerResponse.RESCHEDULE:
            return self._handle_reschedule(context)
        elif predicted_response == CustomerResponse.NEED_INFO:
            return self._handle_objections(context, customer_response)
        else:
            return self._handle_uncertain(context)
    
    def _select_channel(
        self,
        urgency: UrgencyLevel,
        profile: CustomerProfile
    ) -> CommunicationChannel:
        """Select appropriate communication channel"""
        if urgency == UrgencyLevel.CRITICAL:
            return CommunicationChannel.PHONE_CALL
        elif urgency == UrgencyLevel.URGENT:
            return CommunicationChannel.PHONE_CALL if profile.preferred_channel == CommunicationChannel.PHONE_CALL else CommunicationChannel.SMS
        else:
            return profile.preferred_channel
    
    def _generate_greeting(self, context: ConversationContext) -> str:
        """Generate personalized greeting"""
        profile = context.customer_profile
        style = profile.communication_style
        
        templates = self.dialogue_templates['greeting'].get(style, self.dialogue_templates['greeting']['formal'])
        template = random.choice(templates)
        
        time_of_day = self._get_time_of_day()
        
        return template.format(
            time_of_day=time_of_day,
            name=profile.name,
            agent_name="Sarah",  # Could be dynamic
            company="AutoCare Services"
        )
    
    def _generate_issue_explanation(self, context: ConversationContext) -> str:
        """Generate issue explanation based on urgency"""
        report = context.diagnostic_report
        profile = context.customer_profile
        style = profile.communication_style
        
        # Select template based on urgency
        if report.urgency_level == UrgencyLevel.CRITICAL:
            templates = self.dialogue_templates['critical_issue'][style]
        elif report.urgency_level == UrgencyLevel.URGENT:
            templates = self.dialogue_templates['urgent_issue'][style]
        elif report.urgency_level == UrgencyLevel.PREVENTIVE:
            templates = self.dialogue_templates['preventive'][style]
        else:
            templates = self.dialogue_templates['routine'][style]
        
        template = random.choice(templates)
        
        # Format issue description
        issue_desc = self._format_issue_description(report)
        
        return template.format(
            name=profile.name,
            vehicle=f"{report.vehicle_id}",  # Could include make/model
            issue_description=issue_desc,
            suggested_time="tomorrow morning"
        )
    
    def _format_issue_description(self, report: DiagnosticReport) -> str:
        """Format issue description in natural language"""
        if len(report.issues_detected) == 1:
            return f"a {report.issues_detected[0]} issue"
        elif len(report.issues_detected) == 2:
            return f"{report.issues_detected[0]} and {report.issues_detected[1]} issues"
        else:
            issues = ", ".join(report.issues_detected[:-1])
            return f"{issues}, and {report.issues_detected[-1]} issues"
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of customer message
        
        Returns:
            float: Sentiment score from -1 (negative) to 1 (positive)
        """
        if self.sentiment_model and self.sentiment_tokenizer:
            try:
                inputs = self.sentiment_tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                )
                
                with torch.no_grad():
                    outputs = self.sentiment_model(**inputs)
                    scores = torch.softmax(outputs.logits, dim=1)
                    
                # Assuming binary classification: negative (0) and positive (1)
                sentiment = scores[0][1].item() * 2 - 1  # Convert to -1 to 1
                
                return sentiment
                
            except Exception as e:
                logger.error(f"Sentiment analysis error: {e}")
                return self._rule_based_sentiment(text)
        else:
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> float:
        """Rule-based sentiment analysis fallback"""
        text_lower = text.lower()
        
        positive_words = [
            'yes', 'sure', 'okay', 'great', 'good', 'fine', 'thanks',
            'appreciate', 'perfect', 'excellent', 'sounds good'
        ]
        negative_words = [
            'no', 'not', 'never', 'can\'t', 'won\'t', 'don\'t', 'busy',
            'expensive', 'annoyed', 'frustrated', 'angry', 'upset'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _predict_customer_response(
        self,
        text: str,
        context: ConversationContext
    ) -> CustomerResponse:
        """
        Predict customer response type
        
        Args:
            text: Customer message
            context: Conversation context
            
        Returns:
            CustomerResponse: Predicted response type
        """
        text_lower = text.lower()
        
        # Check for clear acceptance
        if any(word in text_lower for word in ['yes', 'sure', 'okay', 'schedule', 'book', 'appointment']):
            return CustomerResponse.ACCEPT
        
        # Check for clear decline
        if any(word in text_lower for word in ['no', 'not interested', 'don\'t want', 'cancel']):
            return CustomerResponse.DECLINE
        
        # Check for reschedule
        if any(word in text_lower for word in ['later', 'another time', 'reschedule', 'different day']):
            return CustomerResponse.RESCHEDULE
        
        # Check for frustration
        if any(word in text_lower for word in ['annoyed', 'frustrated', 'angry', 'stop calling']):
            return CustomerResponse.FRUSTRATED
        
        # Check for need more info
        if any(word in text_lower for word in ['why', 'how much', 'cost', 'explain', 'sure', 'really']):
            return CustomerResponse.NEED_INFO
        
        # Default to uncertain
        return CustomerResponse.UNCERTAIN

    def _should_escalate(self, context: ConversationContext) -> bool:
        """Determine if conversation should be escalated to human"""
        # Low confidence
        if context.confidence_score < self.confidence_threshold:
            logger.info(f"Escalating due to low confidence: {context.confidence_score}")
            return True
        
        # Negative sentiment
        if context.customer_sentiment < self.escalation_sentiment_threshold:
            logger.info(f"Escalating due to negative sentiment: {context.customer_sentiment}")
            return True
        
        # Too many objections
        if context.objections_count >= 3:
            logger.info(f"Escalating due to multiple objections: {context.objections_count}")
            return True
        
        # Customer is frustrated
        if context.predicted_response == CustomerResponse.FRUSTRATED:
            logger.info("Escalating due to customer frustration")
            return True
        
        return False
    
    def _escalate_to_human(self, context: ConversationContext) -> EngagementResult:
        """Escalate conversation to human agent"""
        context.state = ConversationState.ESCALATION
        context.escalation_triggered = True
        
        escalation_message = random.choice(self.dialogue_templates['escalation'])
        self._add_message(context, 'agent', escalation_message)
        
        self.stats['escalations'] += 1
        
        logger.info(f"Escalated conversation {context.conversation_id} to human agent")
        
        return EngagementResult(
            conversation_id=context.conversation_id,
            customer_id=context.customer_profile.customer_id,
            vehicle_id=context.diagnostic_report.vehicle_id,
            outcome=CustomerResponse.NEED_INFO,
            appointment_scheduled=False,
            sentiment_score=context.customer_sentiment,
            escalated_to_human=True,
            conversation_transcript=context.messages
        )
    
    def _handle_acceptance(self, context: ConversationContext) -> EngagementResult:
        """Handle customer acceptance"""
        context.state = ConversationState.SCHEDULING
        
        # Gather preferences
        preferences = self._gather_preferences(context)
        context.preferences_captured = preferences
        
        # Generate appointment details
        appointment = self._generate_appointment(context, preferences)
        
        # Confirmation
        context.state = ConversationState.CONFIRMATION
        confirmation = self._generate_confirmation(context, appointment)
        self._add_message(context, 'agent', confirmation)
        
        # Send notifications
        self._send_notifications(context, appointment)
        
        context.state = ConversationState.COMPLETED
        self.stats['successful_schedules'] += 1
        
        logger.info(f"Successfully scheduled appointment for {context.customer_profile.customer_id}")
        
        return EngagementResult(
            conversation_id=context.conversation_id,
            customer_id=context.customer_profile.customer_id,
            vehicle_id=context.diagnostic_report.vehicle_id,
            outcome=CustomerResponse.ACCEPT,
            appointment_scheduled=True,
            appointment_details=appointment,
            customer_preferences=preferences,
            sentiment_score=context.customer_sentiment,
            conversation_transcript=context.messages
        )
    
    def _handle_decline(self, context: ConversationContext) -> EngagementResult:
        """Handle customer decline"""
        # Try one more time with empathy
        if context.objections_count == 0:
            empathy_message = self._generate_empathy_response(context)
            self._add_message(context, 'agent', empathy_message)
            
            # Simulate response
            customer_response = self._simulate_customer_response(context, "empathy")
            self._add_message(context, 'customer', customer_response)
            
            # Check if they changed their mind
            if 'yes' in customer_response.lower() or 'okay' in customer_response.lower():
                return self._handle_acceptance(context)
        
        # Accept decline gracefully
        decline_message = "I understand. If you change your mind or have any questions, please don't hesitate to reach out. We're here to help. Take care!"
        self._add_message(context, 'agent', decline_message)
        
        context.state = ConversationState.COMPLETED
        self.stats['declined'] += 1
        
        logger.info(f"Customer {context.customer_profile.customer_id} declined service")
        
        return EngagementResult(
            conversation_id=context.conversation_id,
            customer_id=context.customer_profile.customer_id,
            vehicle_id=context.diagnostic_report.vehicle_id,
            outcome=CustomerResponse.DECLINE,
            appointment_scheduled=False,
            sentiment_score=context.customer_sentiment,
            conversation_transcript=context.messages
        )
    
    def _handle_reschedule(self, context: ConversationContext) -> EngagementResult:
        """Handle reschedule request"""
        reschedule_message = "No problem! When would work better for you? We have availability throughout the week."
        self._add_message(context, 'agent', reschedule_message)
        
        # Simulate customer providing alternative time
        customer_response = self._simulate_customer_response(context, "reschedule")
        self._add_message(context, 'customer', customer_response)
        
        # Proceed with scheduling
        return self._handle_acceptance(context)
    
    def _handle_objections(
        self,
        context: ConversationContext,
        customer_message: str
    ) -> EngagementResult:
        """Handle customer objections"""
        context.state = ConversationState.OBJECTION_HANDLING
        context.objections_count += 1
        
        # Identify objection type
        objection_type = self._identify_objection(customer_message)
        
        # Generate response
        objection_response = self._generate_objection_response(context, objection_type)
        self._add_message(context, 'agent', objection_response)
        
        # Simulate customer response
        customer_response = self._simulate_customer_response(context, "objection_handled")
        self._add_message(context, 'customer', customer_response)
        
        # Re-predict response
        predicted = self._predict_customer_response(customer_response, context)
        context.predicted_response = predicted
        
        # Update sentiment
        sentiment = self._analyze_sentiment(customer_response)
        context.customer_sentiment = (context.customer_sentiment + sentiment) / 2
        
        # Check for escalation
        if self._should_escalate(context):
            return self._escalate_to_human(context)
        
        # Handle new response
        if predicted == CustomerResponse.ACCEPT:
            return self._handle_acceptance(context)
        elif predicted == CustomerResponse.DECLINE:
            return self._handle_decline(context)
        else:
            # Too many objections, escalate
            return self._escalate_to_human(context)
    
    def _handle_uncertain(self, context: ConversationContext) -> EngagementResult:
        """Handle uncertain customer response"""
        # Provide more information
        info_message = self._generate_additional_info(context)
        self._add_message(context, 'agent', info_message)
        
        # Simulate response
        customer_response = self._simulate_customer_response(context, "additional_info")
        self._add_message(context, 'customer', customer_response)
        
        # Re-predict
        predicted = self._predict_customer_response(customer_response, context)
        
        if predicted == CustomerResponse.ACCEPT:
            return self._handle_acceptance(context)
        else:
            return self._handle_decline(context)
    
    def _identify_objection(self, text: str) -> str:
        """Identify type of objection"""
        text_lower = text.lower()
        
        for objection_type, patterns in self.objection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return objection_type
        
        return 'general'
    
    def _generate_objection_response(
        self,
        context: ConversationContext,
        objection_type: str
    ) -> str:
        """Generate response to objection"""
        report = context.diagnostic_report
        
        if objection_type == 'cost':
            templates = self.dialogue_templates['cost_objection']
            template = random.choice(templates)
            return template.format(
                cost=f"${report.estimated_cost:.2f}",
                cost_breakdown="parts and labor",
                services=", ".join(report.recommended_services),
                higher_cost=f"${report.estimated_cost * 2:.2f}"
            )
        
        elif objection_type == 'time':
            templates = self.dialogue_templates['time_objection']
            template = random.choice(templates)
            return template.format(duration="2-3")
        
        elif objection_type == 'trust':
            templates = self.dialogue_templates['trust_objection']
            return random.choice(templates)
        
        else:
            return "I understand your concern. Let me provide more details about why this service is important for your vehicle's health and safety."
    
    def _generate_empathy_response(self, context: ConversationContext) -> str:
        """Generate empathetic response to try to re-engage"""
        report = context.diagnostic_report
        
        if report.urgency_level == UrgencyLevel.CRITICAL:
            return f"I completely understand this is unexpected. However, I'm genuinely concerned about your safety. The {report.issues_detected[0]} issue we detected could lead to a dangerous situation. Could we at least schedule a quick inspection so you can see for yourself?"
        else:
            return "I hear you, and I don't want to pressure you. I just want to make sure you have all the information. This is about keeping you safe and avoiding bigger problems down the road. Would you like me to send you the diagnostic report to review?"
    
    def _generate_additional_info(self, context: ConversationContext) -> str:
        """Generate additional information message"""
        report = context.diagnostic_report
        
        return f"Let me give you more details. We detected {self._format_issue_description(report)}. Based on our analysis, if left unaddressed, this could lead to {report.risk_description}. The recommended services are {', '.join(report.recommended_services)}, with an estimated cost of ${report.estimated_cost:.2f}. Does that help clarify things?"
    
    def _gather_preferences(self, context: ConversationContext) -> Dict[str, Any]:
        """Gather customer preferences for scheduling"""
        context.state = ConversationState.PREFERENCE_GATHERING
        
        # Ask for preferences
        pref_message = "Great! Let me find the best time for you. Do you prefer morning, afternoon, or evening appointments?"
        self._add_message(context, 'agent', pref_message)
        
        # Simulate customer response
        customer_response = self._simulate_customer_response(context, "preferences")
        self._add_message(context, 'customer', customer_response)
        
        # Extract preferences
        preferences = {
            'preferred_time': self._extract_time_preference(customer_response),
            'preferred_location': context.customer_profile.preferred_location or 'Main Center',
            'loaner_needed': 'loaner' in customer_response.lower(),
            'urgency': context.diagnostic_report.urgency_level.value
        }
        
        return preferences
    
    def _extract_time_preference(self, text: str) -> str:
        """Extract time preference from text"""
        text_lower = text.lower()
        
        if 'morning' in text_lower or 'early' in text_lower:
            return 'morning'
        elif 'afternoon' in text_lower:
            return 'afternoon'
        elif 'evening' in text_lower or 'late' in text_lower:
            return 'evening'
        else:
            return 'flexible'
    
    def _generate_appointment(
        self,
        context: ConversationContext,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate appointment details"""
        report = context.diagnostic_report
        
        # Determine appointment date based on urgency
        if report.urgency_level == UrgencyLevel.CRITICAL:
            appointment_date = datetime.now() + timedelta(hours=4)
        elif report.urgency_level == UrgencyLevel.URGENT:
            appointment_date = datetime.now() + timedelta(days=1)
        elif report.urgency_level == UrgencyLevel.PREVENTIVE:
            appointment_date = datetime.now() + timedelta(days=7)
        else:
            appointment_date = datetime.now() + timedelta(days=14)
        
        # Adjust time based on preference
        if preferences['preferred_time'] == 'morning':
            appointment_date = appointment_date.replace(hour=9, minute=0)
        elif preferences['preferred_time'] == 'afternoon':
            appointment_date = appointment_date.replace(hour=14, minute=0)
        elif preferences['preferred_time'] == 'evening':
            appointment_date = appointment_date.replace(hour=17, minute=0)
        else:
            appointment_date = appointment_date.replace(hour=10, minute=0)
        
        appointment = {
            'appointment_id': f"APT_{context.conversation_id}",
            'date': appointment_date.strftime('%Y-%m-%d'),
            'time': appointment_date.strftime('%H:%M'),
            'datetime': appointment_date.isoformat(),
            'location': preferences['preferred_location'],
            'services': report.recommended_services,
            'estimated_duration': '2-3 hours',
            'estimated_cost': report.estimated_cost,
            'loaner_vehicle': preferences.get('loaner_needed', False),
            'vehicle_id': report.vehicle_id,
            'customer_id': context.customer_profile.customer_id
        }
        
        return appointment
    
    def _generate_confirmation(
        self,
        context: ConversationContext,
        appointment: Dict[str, Any]
    ) -> str:
        """Generate confirmation message"""
        templates = self.dialogue_templates['confirmation']
        template = random.choice(templates)
        
        return template.format(
            date=appointment['date'],
            time=appointment['time'],
            location=appointment['location'],
            channel=context.customer_profile.preferred_channel.value,
            vehicle=context.diagnostic_report.vehicle_id
        )
    
    def _send_notifications(
        self,
        context: ConversationContext,
        appointment: Dict[str, Any]
    ):
        """Send appointment notifications via multiple channels"""
        profile = context.customer_profile
        
        # Voice confirmation (if phone call)
        if profile.preferred_channel == CommunicationChannel.PHONE_CALL:
            logger.info(f"Voice confirmation sent to {profile.phone}")
        
        # App notification
        app_notification = {
            'type': 'appointment_scheduled',
            'title': 'Service Appointment Confirmed',
            'body': f"Your vehicle service is scheduled for {appointment['date']} at {appointment['time']}",
            'data': appointment
        }
        logger.info(f"App notification sent: {app_notification}")
        
        # SMS backup
        sms_message = f"AutoCare: Your service appointment is confirmed for {appointment['date']} at {appointment['time']} at {appointment['location']}. Reply CANCEL to cancel."
        logger.info(f"SMS sent to {profile.phone}: {sms_message}")
        
        # Email confirmation
        email_subject = "Service Appointment Confirmation"
        email_body = f"""
        Dear {profile.name},
        
        Your service appointment has been confirmed:
        
        Date: {appointment['date']}
        Time: {appointment['time']}
        Location: {appointment['location']}
        Services: {', '.join(appointment['services'])}
        Estimated Cost: ${appointment['estimated_cost']:.2f}
        
        We look forward to serving you!
        
        Best regards,
        AutoCare Services
        """
        logger.info(f"Email sent to {profile.email}")
    
    def _simulate_customer_response(
        self,
        context: ConversationContext,
        stage: str
    ) -> str:
        """
        Simulate customer response for demonstration
        In production, this would be actual customer input
        """
        report = context.diagnostic_report
        sentiment = context.customer_sentiment
        
        # Response patterns based on stage and sentiment
        responses = {
            'greeting': [
                "I'm good, thanks. What's this about?",
                "Hi, I'm a bit busy. What do you need?",
                "Hello. Is everything okay?"
            ],
            'issue_explanation': {
                'critical': [
                    "Oh no, that sounds serious! Yes, let's schedule something right away.",
                    "Really? How bad is it? Can I still drive it?",
                    "This is unexpected. How much will this cost?"
                ],
                'urgent': [
                    "Okay, I should probably get that checked. When can you fit me in?",
                    "Hmm, I'm pretty busy this week. Is it really urgent?",
                    "How much are we talking about for the repair?"
                ],
                'preventive': [
                    "That makes sense. Better safe than sorry. Let's schedule it.",
                    "I appreciate the heads up. Can we do it next week?",
                    "Is this really necessary? The car seems fine to me."
                ],
                'routine': [
                    "Oh right, it's been a while. Sure, let's set something up.",
                    "Can we do this next month? I'm swamped right now.",
                    "How much is the service going to cost?"
                ]
            },
            'objection_handled': [
                "Okay, that makes sense. Let's go ahead and schedule it.",
                "I'm still not sure. Can I think about it?",
                "Alright, you've convinced me. When's the earliest you can take me?"
            ],
            'preferences': [
                "Morning works best for me, around 9 AM if possible.",
                "I prefer afternoons. Also, do you have loaner vehicles?",
                "Evening would be great, after 5 PM."
            ],
            'reschedule': [
                "How about next Tuesday morning?",
                "Can we do it next week instead?",
                "I'm free Thursday afternoon."
            ],
            'empathy': [
                "I appreciate your concern. Okay, let's schedule it.",
                "I understand, but I really can't right now. Maybe next month?",
                "You're right about safety. Let's do it."
            ],
            'additional_info': [
                "Thanks for explaining. Yes, let's schedule the service.",
                "I see. Let me think about it and call you back.",
                "Okay, that helps. When can you fit me in?"
            ]
        }
        
        # Select response based on stage
        if stage == 'issue_explanation':
            urgency = report.urgency_level.value
            if urgency == 'critical':
                options = responses['issue_explanation']['critical']
            elif urgency == 'urgent':
                options = responses['issue_explanation']['urgent']
            elif urgency == 'preventive':
                options = responses['issue_explanation']['preventive']
            else:
                options = responses['issue_explanation']['routine']
        else:
            options = responses.get(stage, ["Okay, I understand."])
        
        # Bias selection based on sentiment and urgency
        if report.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.URGENT]:
            # More likely to accept for urgent issues
            return options[0] if len(options) > 0 else "Yes, let's schedule it."
        else:
            return random.choice(options)
    
    def _add_message(
        self,
        context: ConversationContext,
        role: str,
        message: str
    ):
        """Add message to conversation history"""
        context.messages.append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def _get_time_of_day(self) -> str:
        """Get appropriate greeting based on time"""
        hour = datetime.now().hour
        
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def get_conversation_transcript(self, conversation_id: str) -> Optional[List[Dict[str, str]]]:
        """Get conversation transcript"""
        context = self.active_conversations.get(conversation_id)
        return context.messages if context else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        if self.stats['total_engagements'] > 0:
            self.stats['success_rate'] = self.stats['successful_schedules'] / self.stats['total_engagements']
            self.stats['escalation_rate'] = self.stats['escalations'] / self.stats['total_engagements']
        
        return self.stats


# Integration with Master Orchestrator
def create_customer_engagement_handler(agent: CustomerEngagementAgent):
    """
    Create handler function for Master Orchestrator integration
    
    Args:
        agent: CustomerEngagementAgent instance
        
    Returns:
        Handler function compatible with orchestrator
    """
    def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler for Master Orchestrator
        
        Args:
            payload: Contains diagnosis_results and customer info
            
        Returns:
            Engagement results dictionary
        """
        # Extract data from payload
        vehicle_id = payload['vehicle_id']
        diagnosis = payload.get('diagnosis_results', {})
        urgency_score = payload.get('urgency_score', 0.5)
        
        # Determine urgency level
        if urgency_score > 0.7:
            urgency = UrgencyLevel.CRITICAL
        elif urgency_score > 0.5:
            urgency = UrgencyLevel.URGENT
        elif urgency_score > 0.3:
            urgency = UrgencyLevel.PREVENTIVE
        else:
            urgency = UrgencyLevel.ROUTINE
        
        # Create diagnostic report
        diagnostic_report = DiagnosticReport(
            vehicle_id=vehicle_id,
            customer_id=payload.get('customer_id', f'CUST_{vehicle_id}'),
            urgency_level=urgency,
            issues_detected=diagnosis.get('predicted_failures', ['general_maintenance']),
            recommended_services=diagnosis.get('recommended_services', ['inspection']),
            estimated_cost=diagnosis.get('estimated_cost', 250.0),
            risk_description=diagnosis.get('risk_description', 'potential vehicle issues'),
            time_to_failure_days=diagnosis.get('estimated_days_to_failure'),
            safety_critical=urgency == UrgencyLevel.CRITICAL
        )
        
        # Create customer profile (in production, fetch from database)
        customer_profile = CustomerProfile(
            customer_id=diagnostic_report.customer_id,
            name=payload.get('customer_name', 'Valued Customer'),
            phone=payload.get('customer_phone', '+1-555-0100'),
            email=payload.get('customer_email', 'customer@example.com'),
            preferred_channel=CommunicationChannel.PHONE_CALL if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.URGENT] else CommunicationChannel.EMAIL,
            preferred_time='morning',
            communication_style='formal'
        )
        
        # Engage customer
        result = agent.engage_customer(diagnostic_report, customer_profile)
        
        # Convert to dict for orchestrator
        return result.to_dict()
    
    return handler


# Example usage and testing
if __name__ == "__main__":
    import time
    
    print("="*70)
    print(" CUSTOMER ENGAGEMENT AGENT - DEMONSTRATION")
    print("="*70)
    print()
    
    # Initialize agent
    agent = CustomerEngagementAgent()
    
    # Test Scenario 1: Critical Issue
    print("\n" + "="*70)
    print(" SCENARIO 1: CRITICAL ENGINE ISSUE")
    print("="*70 + "\n")
    
    critical_report = DiagnosticReport(
        vehicle_id='VEH001',
        customer_id='CUST001',
        urgency_level=UrgencyLevel.CRITICAL,
        issues_detected=['engine overheating', 'coolant system failure'],
        recommended_services=['cooling_system_repair', 'thermostat_replacement'],
        estimated_cost=850.00,
        risk_description='potential engine damage and safety hazard',
        time_to_failure_days=1,
        safety_critical=True
    )
    
    customer1 = CustomerProfile(
        customer_id='CUST001',
        name='John Smith',
        phone='+1-555-0101',
        email='john.smith@example.com',
        preferred_channel=CommunicationChannel.PHONE_CALL,
        preferred_time='morning',
        communication_style='formal'
    )
    
    result1 = agent.engage_customer(critical_report, customer1)
    
    print("\n--- Conversation Transcript ---")
    for msg in result1.conversation_transcript:
        role = msg['role'].upper()
        print(f"\n[{role}]: {msg['message']}")
    
    print(f"\n--- Result ---")
    print(f"Outcome: {result1.outcome.value}")
    print(f"Appointment Scheduled: {result1.appointment_scheduled}")
    print(f"Sentiment Score: {result1.sentiment_score:.2f}")
    print(f"Escalated: {result1.escalated_to_human}")
    
    if result1.appointment_details:
        print(f"\nAppointment Details:")
        print(f"  Date: {result1.appointment_details['date']}")
        print(f"  Time: {result1.appointment_details['time']}")
        print(f"  Location: {result1.appointment_details['location']}")
    
    # Test Scenario 2: Routine Maintenance
    print("\n\n" + "="*70)
    print(" SCENARIO 2: ROUTINE MAINTENANCE")
    print("="*70 + "\n")
    
    routine_report = DiagnosticReport(
        vehicle_id='VEH002',
        customer_id='CUST002',
        urgency_level=UrgencyLevel.ROUTINE,
        issues_detected=['scheduled_maintenance_due'],
        recommended_services=['oil_change', 'tire_rotation', 'inspection'],
        estimated_cost=150.00,
        risk_description='maintain vehicle health',
        time_to_failure_days=None,
        safety_critical=False
    )
    
    customer2 = CustomerProfile(
        customer_id='CUST002',
        name='Sarah Johnson',
        phone='+1-555-0102',
        email='sarah.j@example.com',
        preferred_channel=CommunicationChannel.EMAIL,
        preferred_time='afternoon',
        communication_style='casual'
    )
    
    result2 = agent.engage_customer(routine_report, customer2)
    
    print("\n--- Conversation Transcript ---")
    for msg in result2.conversation_transcript:
        role = msg['role'].upper()
        print(f"\n[{role}]: {msg['message']}")
    
    print(f"\n--- Result ---")
    print(f"Outcome: {result2.outcome.value}")
    print(f"Appointment Scheduled: {result2.appointment_scheduled}")
    print(f"Sentiment Score: {result2.sentiment_score:.2f}")
    
    # Statistics
    print("\n\n" + "="*70)
    print(" AGENT STATISTICS")
    print("="*70 + "\n")
    
    stats = agent.get_statistics()
    print(f"Total Engagements: {stats['total_engagements']}")
    print(f"Successful Schedules: {stats['successful_schedules']}")
    print(f"Escalations: {stats['escalations']}")
    print(f"Declined: {stats['declined']}")
    if 'success_rate' in stats:
        print(f"Success Rate: {stats['success_rate']*100:.1f}%")
    if 'escalation_rate' in stats:
        print(f"Escalation Rate: {stats['escalation_rate']*100:.1f}%")
    
    print("\n" + "="*70)
    print(" Demonstration Complete!")
    print("="*70 + "\n")
