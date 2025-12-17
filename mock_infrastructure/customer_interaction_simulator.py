"""
Customer Interaction Layer
Simulates voice/chat responses for customer engagement
"""
import random
from typing import Dict, Any, List
from datetime import datetime


class CustomerInteractionSimulator:
    """Simulates customer responses to service notifications"""
    
    # Customer personality types
    PERSONALITIES = {
        "cooperative": {
            "acceptance_rate": 0.8,
            "response_time_minutes": 30,
            "sentiment": "positive"
        },
        "busy": {
            "acceptance_rate": 0.5,
            "response_time_minutes": 180,
            "sentiment": "neutral"
        },
        "skeptical": {
            "acceptance_rate": 0.3,
            "response_time_minutes": 60,
            "sentiment": "negative"
        },
        "enthusiastic": {
            "acceptance_rate": 0.9,
            "response_time_minutes": 15,
            "sentiment": "positive"
        }
    }
    
    def __init__(self, customer_name: str, personality: str = None):
        self.customer_name = customer_name
        self.personality = personality or random.choice(list(self.PERSONALITIES.keys()))
        self.personality_traits = self.PERSONALITIES[self.personality]
        self.interaction_history = []
    
    def receive_notification(
        self,
        notification_type: str,
        message: str,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """Simulate receiving a notification"""
        
        # Determine if customer will respond
        will_respond = random.random() < 0.9  # 90% response rate
        
        if not will_respond:
            return {
                "responded": False,
                "response_time_minutes": None,
                "response": None
            }
        
        # Simulate response time
        base_time = self.personality_traits["response_time_minutes"]
        if urgency == "urgent":
            response_time = base_time * 0.5
        elif urgency == "high":
            response_time = base_time * 0.7
        else:
            response_time = base_time
        
        response_time += random.randint(-10, 30)
        
        # Generate response
        response = self._generate_response(notification_type, message, urgency)
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "notification_type": notification_type,
            "message": message,
            "urgency": urgency,
            "responded": True,
            "response_time_minutes": max(5, response_time),
            "response": response
        }
        
        self.interaction_history.append(interaction)
        
        return interaction
    
    def _generate_response(
        self,
        notification_type: str,
        message: str,
        urgency: str
    ) -> Dict[str, Any]:
        """Generate customer response"""
        
        # Determine acceptance
        acceptance_rate = self.personality_traits["acceptance_rate"]
        
        # Increase acceptance for urgent issues
        if urgency == "urgent":
            acceptance_rate = min(1.0, acceptance_rate + 0.2)
        elif urgency == "high":
            acceptance_rate = min(1.0, acceptance_rate + 0.1)
        
        will_accept = random.random() < acceptance_rate
        
        if will_accept:
            return self._generate_acceptance_response(urgency)
        else:
            return self._generate_decline_response()
    
    def _generate_acceptance_response(self, urgency: str) -> Dict[str, Any]:
        """Generate acceptance response"""
        
        responses_by_personality = {
            "cooperative": [
                "Thank you for letting me know. I'll schedule an appointment right away.",
                "I appreciate the heads up. When can I bring it in?",
                "That's concerning. Please book me for the earliest available slot."
            ],
            "busy": [
                "Okay, I can probably fit this in next week.",
                "Alright, but I'm pretty busy. What's the soonest I can come in?",
                "Fine, I'll make time for this."
            ],
            "skeptical": [
                "I guess I should get this checked out.",
                "Are you sure this is necessary? Well, okay.",
                "I'll schedule something, but I want a second opinion."
            ],
            "enthusiastic": [
                "Oh wow, thanks for catching that! Let's get it fixed ASAP!",
                "I really appreciate the proactive notification. Book me in!",
                "This is exactly why I love this service! When can you see me?"
            ]
        }
        
        text = random.choice(responses_by_personality[self.personality])
        
        # Preferred dates
        preferred_dates = []
        if urgency == "urgent":
            preferred_dates = ["tomorrow", "as soon as possible"]
        elif urgency == "high":
            preferred_dates = ["this week", "within 3 days"]
        else:
            preferred_dates = ["next week", "within 2 weeks"]
        
        return {
            "decision": "accepted",
            "text": text,
            "sentiment": self.personality_traits["sentiment"],
            "preferred_dates": preferred_dates,
            "preferred_time": random.choice(["morning", "afternoon", "evening"]),
            "preferred_location": random.choice(["nearest", "downtown", "specific_center"])
        }
    
    def _generate_decline_response(self) -> Dict[str, Any]:
        """Generate decline response"""
        
        decline_reasons = [
            "I just had it serviced recently.",
            "I can't afford this right now.",
            "I'm too busy this month.",
            "I'll wait and see if it gets worse.",
            "I have a mechanic I prefer to use.",
            "I'm planning to sell the car soon anyway."
        ]
        
        responses_by_personality = {
            "cooperative": [
                "I appreciate the notification, but I'll have to pass for now.",
                "Thanks, but I think I'll wait a bit longer."
            ],
            "busy": [
                "I really don't have time for this right now.",
                "Can this wait? I'm swamped."
            ],
            "skeptical": [
                "I don't think this is as urgent as you're making it sound.",
                "I'll get a second opinion first."
            ],
            "enthusiastic": [
                "Oh no, I wish I could, but I'm traveling!",
                "Darn, bad timing. Can we reschedule for next month?"
            ]
        }
        
        text = random.choice(responses_by_personality[self.personality])
        reason = random.choice(decline_reasons)
        
        return {
            "decision": "declined",
            "text": text,
            "reason": reason,
            "sentiment": self.personality_traits["sentiment"],
            "reschedule_interest": random.random() < 0.5
        }
    
    def simulate_chat_conversation(
        self,
        initial_message: str
    ) -> List[Dict[str, str]]:
        """Simulate a chat conversation"""
        
        conversation = [
            {"role": "agent", "message": initial_message}
        ]
        
        # Customer's first response
        if "urgent" in initial_message.lower() or "critical" in initial_message.lower():
            customer_response = "Oh no, that sounds serious! What should I do?"
        elif "recommend" in initial_message.lower():
            customer_response = "Thanks for letting me know. Tell me more."
        else:
            customer_response = "Okay, I'm listening."
        
        conversation.append({"role": "customer", "message": customer_response})
        
        # Agent provides details
        agent_detail = "Based on our analysis, we recommend scheduling a service appointment soon to prevent potential issues."
        conversation.append({"role": "agent", "message": agent_detail})
        
        # Customer decides
        if random.random() < self.personality_traits["acceptance_rate"]:
            customer_decision = "Alright, let's schedule an appointment. When are you available?"
            conversation.append({"role": "customer", "message": customer_decision})
            
            agent_scheduling = "Great! I can see several available slots this week. Would morning or afternoon work better for you?"
            conversation.append({"role": "agent", "message": agent_scheduling})
            
            customer_preference = f"I prefer {random.choice(['morning', 'afternoon'])} appointments."
            conversation.append({"role": "customer", "message": customer_preference})
        else:
            customer_decision = "I appreciate the information, but I'll have to think about it."
            conversation.append({"role": "customer", "message": customer_decision})
            
            agent_followup = "No problem! Feel free to reach out when you're ready. We're here to help."
            conversation.append({"role": "agent", "message": agent_followup})
        
        return conversation
    
    def simulate_voice_call(
        self,
        call_purpose: str
    ) -> Dict[str, Any]:
        """Simulate a voice call interaction"""
        
        # Call answered?
        answered = random.random() < 0.7  # 70% answer rate
        
        if not answered:
            return {
                "answered": False,
                "voicemail_left": True,
                "callback_requested": random.random() < 0.8
            }
        
        # Call duration
        duration_seconds = random.randint(60, 300)
        
        # Call outcome
        if random.random() < self.personality_traits["acceptance_rate"]:
            outcome = "appointment_scheduled"
            appointment_confirmed = True
        else:
            outcome = random.choice(["declined", "callback_later", "more_info_needed"])
            appointment_confirmed = False
        
        return {
            "answered": True,
            "duration_seconds": duration_seconds,
            "outcome": outcome,
            "appointment_confirmed": appointment_confirmed,
            "customer_sentiment": self.personality_traits["sentiment"],
            "notes": f"Customer was {self.personality}. {outcome.replace('_', ' ').title()}."
        }
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get summary of all interactions"""
        
        total_interactions = len(self.interaction_history)
        responded = sum(1 for i in self.interaction_history if i["responded"])
        
        return {
            "customer_name": self.customer_name,
            "personality": self.personality,
            "total_interactions": total_interactions,
            "response_rate": responded / total_interactions if total_interactions > 0 else 0,
            "avg_response_time_minutes": sum(
                i["response_time_minutes"] for i in self.interaction_history if i["responded"]
            ) / responded if responded > 0 else 0,
            "acceptance_rate": sum(
                1 for i in self.interaction_history 
                if i["responded"] and i["response"]["decision"] == "accepted"
            ) / responded if responded > 0 else 0
        }


def demo_customer_interactions():
    """Demonstrate customer interaction simulation"""
    print("="*80)
    print("CUSTOMER INTERACTION SIMULATOR DEMO")
    print("="*80)
    
    # Create customers with different personalities
    customers = [
        CustomerInteractionSimulator("John Smith", "cooperative"),
        CustomerInteractionSimulator("Sarah Johnson", "busy"),
        CustomerInteractionSimulator("Mike Williams", "skeptical"),
        CustomerInteractionSimulator("Emma Davis", "enthusiastic")
    ]
    
    # Simulate notifications
    notification = {
        "type": "maintenance_alert",
        "message": "Your vehicle's brake pads are at 15% remaining. We recommend scheduling service within 2 weeks.",
        "urgency": "high"
    }
    
    print("\nSending notification to customers...")
    print(f"Message: {notification['message']}")
    print(f"Urgency: {notification['urgency']}")
    
    for customer in customers:
        print(f"\n{'-'*80}")
        print(f"Customer: {customer.customer_name} (Personality: {customer.personality})")
        
        response = customer.receive_notification(
            notification["type"],
            notification["message"],
            notification["urgency"]
        )
        
        if response["responded"]:
            print(f"  Responded in: {response['response_time_minutes']} minutes")
            print(f"  Decision: {response['response']['decision']}")
            print(f"  Response: {response['response']['text']}")
            print(f"  Sentiment: {response['response']['sentiment']}")
        else:
            print("  Did not respond")
    
    # Simulate chat conversation
    print(f"\n{'='*80}")
    print("CHAT CONVERSATION SIMULATION")
    print(f"{'='*80}")
    
    customer = customers[0]
    conversation = customer.simulate_chat_conversation(
        "Hello! We've detected that your vehicle may need attention soon."
    )
    
    for message in conversation:
        role = message["role"].upper()
        print(f"\n{role}: {message['message']}")
    
    # Simulate voice call
    print(f"\n{'='*80}")
    print("VOICE CALL SIMULATION")
    print(f"{'='*80}")
    
    call_result = customer.simulate_voice_call("schedule_maintenance")
    print(f"\nCall Result:")
    print(f"  Answered: {call_result['answered']}")
    if call_result['answered']:
        print(f"  Duration: {call_result['duration_seconds']} seconds")
        print(f"  Outcome: {call_result['outcome']}")
        print(f"  Appointment Confirmed: {call_result['appointment_confirmed']}")
        print(f"  Notes: {call_result['notes']}")


if __name__ == "__main__":
    demo_customer_interactions()
