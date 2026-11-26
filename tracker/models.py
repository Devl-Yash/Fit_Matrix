from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# =============================
# PROFILE MODEL
# =============================
class Profile(models.Model):
    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('gain', 'Gain Weight'),
        ('maintain', 'Maintain Weight'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.FloatField()  # Current weight
    height = models.FloatField()  # In cm
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    
    # Water tracking fields
    water_goal = models.IntegerField(default=8)
    water_consumed = models.IntegerField(default=0)

    # -------- BMI Calculation --------
    def calculate_bmi(self):
        try:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        except (ZeroDivisionError, TypeError):
            return 0

    # -------- BMR Calculation (Mifflin-St Jeor Equation) --------
    def calculate_bmr(self):
        try:
            if self.gender == 'M':
                return (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
            return (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161
        except TypeError:
            return 0

    def __str__(self):
        return f"{self.user.username}'s Profile"

# =============================
# FOOD LOG (With Macros)
# =============================
class FoodLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=100)
    calories = models.IntegerField()
    protein = models.IntegerField(default=0)
    carbs = models.IntegerField(default=0)
    fats = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_name} ({self.calories} kcal)"

# =============================
# WEIGHT HISTORY
# =============================
class WeightHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField()
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'date') # Prevents multiple logs per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}: {self.weight}kg on {self.date}"