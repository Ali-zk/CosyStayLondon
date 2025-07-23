# views.py (accounts application views)

from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect, render
from django.views.generic import View, TemplateView
from .models import User, UserType
from django.contrib.auth import login, authenticate

from django.utils.html import format_html
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import random
import json

# Login view
class LoginView(auth_views.LoginView):
    """ Login with email and password """
    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    redirect_authenticated_user = True
    
    def post(self, request, *args, **kwargs):
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                email = data.get('email')
                password = data.get('password')
                
                user = authenticate(request, username=email, password=password)
                if user and user.is_active:
                    if user.is_verified:
                        login(request, user)
                        messages.success(request, "Sign in successfully.")
                        return JsonResponse({
                            'success': True, 
                            'redirect_url': self.get_success_url()
                        })
                    else:
                        request.session["unverified_user_email"] = user.email
                        return JsonResponse({
                            'success': False,
                            'message': 'Your account has not been verified yet.',
                            'redirect_url': reverse('accounts:verify_email')
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid email or password.'
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data.'
                }, status=400)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        if self.request.user.is_verified:
            return super().get_success_url()
        else:
            messages.warning(self.request, "Your account has not been verified yet. Please verify your email.")
            return reverse('accounts:verify_email')
    
class LogoutView(auth_views.LogoutView):
    pass
    
# generate verification code
def generate_verification_code():
    """ Create a 6-num code """
    return str(random.randint(100000, 999999))

# send verification email function
def send_verification_email(user_email, code):
    """ Sends email containing verification code with attractive design. """
    subject = 'Your Verification Code - Registration'
    
    # HTML email content with inline styles
    html_message = format_html(f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f7f7f7; padding: 20px 0; display: flex; justify-content: center; align-items: center; min-height: 100vh;">
        <div style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); padding: 30px; max-width: 500px; width: 90%;">
            <h2 style="font-size: 24px; font-weight: 600; color: #333; text-align: center; margin-bottom: 20px;">Email Verification</h2>
            <p style="color: #666; text-align: center; margin-bottom: 25px;">
                Hello there,
            </p>
            <p style="color: #666; text-align: center; margin-bottom: 25px;">
                Thank you for registering with us! To complete your registration and verify your email, please use the following verification code:
            </p>
            <div style="text-align: center; margin-bottom: 30px;">
                <span style="display: inline-block; padding: 15px 30px; background-color: #6a0dad; color: #ffffff; font-size: 32px; font-weight: bold; letter-spacing: 4px; border-radius: 8px;">
                    {code}
                </span>
            </div>
            <p style="color: #666; text-align: center; margin-bottom: 20px;">
                This code is valid for a limited time. Please do not share this code with anyone.
            </p>
            <p style="color: #666; text-align: center; font-size: 14px;">
                If you did not request this code, please ignore this email.
            </p>
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 13px; color: #888;">
                Best regards,<br/>
                Your Team
            </div>
        </div>
    </div>
    """)
    
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]
    
    send_mail(
        subject,
        '', # Leave text message empty since we have HTML message
        email_from,
        recipient_list,
        html_message=html_message, # Send HTML message
        fail_silently=False,
    )
    
# Register view
class RegisterView(TemplateView):
    """ First, it puts email in json data. then it checks if email exists or not. """
    template_name = "accounts/register.html"
    
    def post(self, request, *args, **kwargs):
        """ Get verification code and checks it """
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            
            if not email:
                return JsonResponse({"success" : False, "message": "Please enter your email!"}, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({"success" : False, "message": "The email has been already registered!"}, status=400)
            
            user_type = UserType.customer.value
            
            user = User.objects.create_user(
                email=email,
                password=password,
                type=user_type,
            )
            
            verification_code = generate_verification_code()
            send_verification_email(user.email, verification_code)
            
            request.session["unverified_user_email"] = user.email
            request.session['verification_code'] = verification_code
            request.session['code_sent_at'] = timezone.now().timestamp()

            messages.info(request, "The verification code has been sent to your email. Please Enter the code")
            return JsonResponse({'success': True, 'redirect_url': reverse('accounts:verify_email')})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON response!'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

        
class VerifyEmailView(View):
    """ Sends verification code to email and then checks if the user enters correct code. """
    template_name = 'accounts/verify_email.html'

    def get(self, request, *args, **kwargs):
        user_email = request.session.get('unverified_user_email')
        if not user_email:
            messages.error(request, "The email has not found!!!")
            return redirect(reverse('accounts:login'))
        return render(request, self.template_name, {'email': user_email})

    def post(self, request, *args, **kwargs):
        user_email = request.session.get('unverified_user_email')
        stored_code = request.session.get('verification_code')

        if not user_email or not stored_code:
            messages.error(request, "Error in verification process. Please register again.")
            return redirect(reverse('accounts:login'))

        entered_code = request.POST.get('verification_code')

        if entered_code == stored_code:
            try:
                user = User.objects.get(email=user_email)
                user.is_verified = True
                user.save()

                del request.session['unverified_user_email']
                del request.session['verification_code']
                if 'code_sent_at' in request.session:
                    del request.session['code_sent_at']

                messages.success(request, "Your account has been successfully verified. You can now log in.")
                return redirect(reverse('accounts:login'))
            except User.DoesNotExist:
                messages.error(request, "Error: The user was not found.")
                return redirect(reverse('accounts:login'))
        else:
            messages.error(request, "The verification code is incorrect. Please try again.")
            return render(request, self.template_name, {'email': user_email})
        
@require_POST
def resend_verification_code(request):
    user_email = request.session.get('unverified_user_email')
    code_sent_at_timestamp = request.session.get('code_sent_at')

    if not user_email:
        return JsonResponse({'success': False, 'message': 'Can not find this account to resend the code'}, status=400)

    if code_sent_at_timestamp:
        last_sent_time = timezone.datetime.fromtimestamp(code_sent_at_timestamp, tz=timezone.utc)
        current_time = timezone.now()
        time_difference = (current_time - last_sent_time).total_seconds()
        
        if time_difference < 60:
            remaining_time = int(60 - time_difference)
            return JsonResponse({'success': False, 'message': f'Please wait about {remaining_time} to resend verification code'}, status=429)

    try:
        user = User.objects.get(email=user_email, is_verified=False) #
        verification_code = generate_verification_code()
        send_verification_email(user.email, verification_code)

        request.session['verification_code'] = verification_code
        request.session['code_sent_at'] = timezone.now().timestamp()
        
        return JsonResponse({'success': True, 'message': 'The new code has been sent.'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User has not found or has been verified.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error to resending code: {str(e)}'}, status=500)
