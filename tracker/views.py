import google.generativeai as genai
from PIL import Image
import os
import re
import json

from dotenv import load_dotenv
load_dotenv()
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from .models import Profile, FoodLog, WeightHistory
from .forms import RegisterForm, ProfileForm, FoodUploadForm

# 🔑 Configure Gemini API
api_key = os.getenv("EXTERNAL_API_KEY")

# =============================
# REGISTER
# =============================
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('profile_setup')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# =============================
# PROFILE SETUP
# =============================
@login_required
def profile_setup(request):
    # 1. Look for an existing profile, but DON'T try to create one yet
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        # 2. If profile exists, 'instance' updates it. If None, it creates it.
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            # 3. Create the object in memory, assign the user, then save to DB
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect('dashboard')
        else:
            # This will show you in the console if validation failed
            print(form.errors)
    else:
        # 4. GET request: Show the form (blank or with existing data)
        form = ProfileForm(instance=profile)

    return render(request, 'profile_setup.html', {'form': form})

# =============================
# DASHBOARD
# =============================
@login_required
def dashboard(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect('profile_setup')

    today = timezone.now().date()
    food_logs = FoodLog.objects.filter(user=request.user, date=today).order_by('-id')

    # --- CALORIE & MACRO LOGIC ---
    totals = food_logs.aggregate(
        tcals=Sum('calories'),
        tprot=Sum('protein'),
        tcarb=Sum('carbs'),
        tfat=Sum('fats')
    )

    consumed_cals = totals['tcals'] or 0
    consumed_prot = totals['tprot'] or 0
    consumed_carb = totals['tcarb'] or 0
    consumed_fat = totals['tfat'] or 0

    # AI-Derived Targets based on BMR
    target_cals = int(profile.calculate_bmr())
    # Standard Macro Split: 30% Protein, 40% Carbs, 30% Fats
    target_prot = int((target_cals * 0.30) / 4)
    target_carb = int((target_cals * 0.40) / 4)
    target_fat = int((target_cals * 0.30) / 9)

    # --- BMI COLOR COORDINATION LOGIC ---
    bmi = profile.calculate_bmi()
    if bmi < 18.5:
        bmi_color = "text-yellow-500"  # Underweight
    elif 18.5 <= bmi <= 24.9:
        bmi_color = "text-emerald-500" # Healthy Weight
    elif 25.0 <= bmi <= 29.9:
        bmi_color = "text-yellow-500"  # Overweight
    else:
        bmi_color = "text-red-500"     # Obese

    # --- WATER LOGIC ---
    water_consumed = getattr(profile, 'water_consumed', 0)
    water_goal = getattr(profile, 'water_goal', 8)

    # --- WEIGHT LOGIC ---
    weight_history = WeightHistory.objects.filter(user=request.user).order_by('-date')[:7][::-1]
    weight_logged_today = WeightHistory.objects.filter(user=request.user, date=today).exists()

    context = {
        'profile': profile,
        'bmi': bmi,
        'bmi_color': bmi_color,
        'bmr': target_cals,
        'consumed_cals': consumed_cals,
        'target_cals': target_cals,
        'consumed_prot': consumed_prot,
        'target_prot': target_prot,
        'consumed_carb': consumed_carb,
        'target_carb': target_carb,
        'consumed_fat': consumed_fat,
        'target_fat': target_fat,
        'water_consumed': water_consumed,
        'water_goal': water_goal,
        'food_logs': food_logs,
        'weight_history': weight_history,
        'weight_logged_today': weight_logged_today,
    }

    return render(request, 'dashboard.html', context)


# * ADD FOOD (AI MACRO DETECTION)

@login_required
def add_food(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            # Updated to Gemini 3 Flash
            model = genai.GenerativeModel('gemini-3-flash-preview')
            img = Image.open(image_file)

            # Strict Macro Prompt
            prompt = "Identify this food. Return ONLY in this format: 'Name | Calories | Protein_g | Carbs_g | Fats_g'. Example: 'Chicken Salad | 350 | 30 | 10 | 15'"
            
            response = model.generate_content([prompt, img])
            ai_text = response.text.strip()

            # Parsing the data
            parts = ai_text.split('|')
            if len(parts) >= 5:
                food_name = parts[0].strip()
                cals = int(re.search(r'\d+', parts[1]).group())
                prot = int(re.search(r'\d+', parts[2]).group())
                carb = int(re.search(r'\d+', parts[3]).group())
                fat = int(re.search(r'\d+', parts[4]).group())

                FoodLog.objects.create(
                    user=request.user,
                    food_name=food_name[:100],
                    calories=cals,
                    protein=prot,
                    carbs=carb,
                    fats=fat,
                    date=timezone.now().date()
                )
                messages.success(request, f"Logged {food_name}")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"AI Error: {str(e)}")
            return redirect('dashboard')

    return render(request, 'add_food.html', {'form': FoodUploadForm()})

# =============================
# HOME / DIET / WEIGHT / PROFILE
# =============================
def home(request):
    return render(request, "home.html")

@login_required
def diet_plan(request):
    profile = request.user.profile
    bmi = profile.calculate_bmi()
    bmr = profile.calculate_bmr()
    target = "Maintenance"
    if bmi < 18.5: target = "Weight Gain"
    elif bmi > 25: target = "Weight Loss"

    try:
        # Updated to Gemini 3 Flash
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"Create a daily diet plan for BMI: {bmi:.1f}, BMR: {bmr:.0f}, Goal: {target}. Format: BREAKFAST, LUNCH, DINNER with emojis."
        response = model.generate_content(prompt)
        ai_diet = response.text
    except:
        ai_diet = "AI Offline. Plan: Oats, Salad, Veggies."

    return render(request, 'diet_plan.html', {'ai_diet': ai_diet, 'target': target, 'bmi': bmi})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    profile = Profile.objects.get(user=request.user)
    context = {"profile": profile, "bmi": profile.calculate_bmi(), "bmr": profile.calculate_bmr()}
    return render(request, "profile.html", context)

@login_required
def edit_profile(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "edit_profile.html", {"form": form, "profile": profile})

@login_required
def update_weight(request):
    if request.method == "POST":
        today = timezone.now().date()
        new_weight = request.POST.get('weight')
        WeightHistory.objects.get_or_create(user=request.user, date=today, defaults={'weight': new_weight})
        profile = request.user.profile
        profile.weight = new_weight
        profile.save()
    return redirect('dashboard')

# =============================
# WATER UPDATE (NEW)
# =============================
@login_required
def update_water(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_count = data.get('count')
            profile = request.user.profile
            profile.water_consumed = new_count
            profile.save()
            return JsonResponse({'status': 'success', 'count': profile.water_consumed})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)