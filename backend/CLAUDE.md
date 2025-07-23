# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Airbnb-like property rental platform built with Django 5.2.2, designed for the European market with integrated Stripe payments. The platform supports property browsing, booking, cart management, and secure payment processing with European compliance (PSD2/SCA, VAT handling).

## Architecture

### Core Applications Structure

**accounts/** - Custom user authentication and profiles
- Uses custom User model with email-based authentication (AUTH_USER_MODEL = 'accounts.User')
- UserType enum: customer (1) and admin (2) 
- Profile model with Iranian phone validation (legacy, but functional)
- Email verification workflow with 6-digit codes

**shop/** - Property management and browsing
- Property model: rental properties with pricing, location, availability dates
- PropertyImage model: multiple images per property
- Booking model: confirmed reservations with guest details and status tracking

**cart/** - Shopping cart and order management
- Cart/CartItem: session-based booking cart system
- Order/OrderItem: confirmed reservations ready for payment
- Payment models: comprehensive payment tracking with European compliance
- StripePaymentService: centralized payment processing with VAT calculation

**dashboard/** - Admin and customer portals
- Separated into admin/ and customer/ subdirectories
- Permission classes: HasAdminAccessPermission, HasCustomerAccessPermission
- Property management, user management, booking tracking

**home/** - Landing page and main site navigation

### Payment System Architecture

The payment system is built around Stripe integration with European market requirements:

- **Payment Flow**: Cart → Checkout → Stripe Payment Intent → Payment Confirmation → Booking Creation
- **European Compliance**: PSD2/SCA support, VAT calculation per EU country, multi-currency support
- **Payment Methods**: Cards, SEPA Direct Debit, Klarna, iDEAL, Bancontact
- **Webhook Processing**: Secure webhook handling with signature verification
- **Models**: Payment, PaymentRefund, PaymentWebhook for comprehensive audit trails

### URL Structure

```
/ - Home page
/accounts/ - Authentication (login, register, verify email)
/shop/ - Property browsing and details
/cart/ - Shopping cart, checkout, payment processing
/dashboard/ - User dashboards (admin and customer views)
/admin/ - Django admin interface
```

### Key Models Relationships

```
User (accounts.User)
├── Profile (one-to-one)
├── Cart (one-to-one)
├── Properties (owned_properties, foreign key)
├── Bookings (bookings_made, foreign key)
└── Orders (foreign key)

Property (shop.Property)
├── PropertyImages (images, foreign key)
├── CartItems (property_item, foreign key)  
├── OrderItems (property_item, foreign key)
└── Bookings (foreign key)

Order (cart.Order)
├── OrderItems (order_items, foreign key)
└── Payments (payments, foreign key)
```

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### Running the Application
```bash
# Development server
python manage.py runserver

# Production server (Gunicorn)
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

### Payment System Setup
The application requires Stripe configuration. Set these environment variables:
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_SECRET_KEY` - Stripe secret key  
- `STRIPE_WEBHOOK_SECRET` - Webhook endpoint secret

**Railway Deployment Commands:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Create superuser on production
railway run python manage.py createsuperuser

# Run management commands on production
railway run python manage.py generate_properties
```

### Management Commands
```bash
# Generate sample properties (custom command)
python manage.py generate_properties
```

## Configuration Notes

### Database
- **Development**: SQLite by default
- **Production**: PostgreSQL via dj-database-url (Railway auto-provides DATABASE_URL)
- Auto-detection: switches to PostgreSQL when DATABASE_URL environment variable is present
- Custom AUTH_USER_MODEL requires fresh migrations if changed
- Connection pooling enabled for production (conn_max_age=600)

### Static Files
- WhiteNoise middleware for static file serving
- Separate static/ and staticfiles/ directories
- Media files stored in media/ directory

### Deployment
- **Primary**: Railway platform (railway.json + nixpacks.toml)
- **Legacy**: Liara platform configuration (liara.json) - Iranian hosting
- PostgreSQL auto-configuration via DATABASE_URL environment variable
- Gunicorn WSGI server with auto-scaling
- CSRF trusted origins configured for Railway domains (.railway.app, .up.railway.app)

### Session-Based Booking Flow
The cart system uses a unique session-based approach:
1. Property selection stores temp data in session
2. User must be logged in to add to cart
3. Session data is transferred to cart models via `add_from_session` view
4. This prevents cart abandonment from logged-out users

### European Market Features
- VAT rates configured for all EU countries in settings.EU_VAT_RATES
- Multi-currency support (EUR, GBP, USD, CHF, NOK, SEK, DKK)
- Country selection in checkout for proper VAT calculation
- PSD2 Strong Customer Authentication compliance

### Permission System
Custom permission mixins in dashboard.permissions:
- `HasCustomerAccessPermission` - restricts to customer-type users
- `HasAdminAccessPermission` - restricts to admin-type users
- Based on UserType enum values in accounts.models

### Templates Structure
Uses Tailwind CSS with Alpine.js for interactivity. Key template patterns:
- base.html with responsive navigation
- Modular cart system with JSON data passing to JavaScript
- Payment forms with Stripe Elements integration
- Separate admin and customer dashboard layouts

## Railway-Specific Configuration

### Build Process
- **Builder**: Nixpacks (automatic Python detection)
- **Build Command**: `python manage.py collectstatic --noinput && python manage.py migrate`
- **Start Command**: `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT`
- **Health Check**: Configured at root path ("/") with 300s timeout

### Required Environment Variables (Production)
```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
SECURE_SSL_REDIRECT=True
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
# DATABASE_URL automatically provided by Railway PostgreSQL
```

### Security Configuration
- CSRF protection configured for Railway domains
- SSL redirect enabled in production
- Proxy headers configured for Railway's load balancer
- ALLOWED_HOSTS includes Railway domains (.railway.app, .up.railway.app)