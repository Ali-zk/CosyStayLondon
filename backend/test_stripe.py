#!/usr/bin/env python
"""
Simple test script to verify Stripe integration
Run this after setting your environment variables
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import stripe
from django.conf import settings

def test_stripe_connection():
    """Test if Stripe credentials are working"""
    print("Testing Stripe Integration...")
    print(f"Publishable Key: {settings.STRIPE_PUBLISHABLE_KEY[:20]}..." if settings.STRIPE_PUBLISHABLE_KEY else "NOT SET")
    print(f"Secret Key: {settings.STRIPE_SECRET_KEY[:20]}..." if settings.STRIPE_SECRET_KEY else "NOT SET")
    
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == 'sk_test_...':
        print("❌ Error: STRIPE_SECRET_KEY not set or still using placeholder")
        return False
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Test API connection by listing payment methods
        payment_methods = stripe.PaymentMethod.list(type="card", limit=1)
        print("✅ Stripe connection successful!")
        print(f"✅ API is responding correctly")
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Error: Invalid Stripe API key")
        return False
    except stripe.error.StripeError as e:
        print(f"❌ Stripe Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    test_stripe_connection()