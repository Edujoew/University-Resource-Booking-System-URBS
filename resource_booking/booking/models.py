from django.db import models

# Create your models here.
class Resource(models.Model):
    """
    Represents a physical resource or space that can be booked.
    """
    
    # Define available choices for the 'type' field
    RESOURCE_CHOICES = [
        ('ROOM', 'Room/Lecture Hall'),
        ('EQUIP', 'Equipment (e.g., Projector, Camera)'),
        ('LAB', 'Laboratory/Specialized Space'),
        ('VEH', 'Vehicle'),
        ('OTHER', 'Other'),
    ]

    # --- 2. Define Model Fields ---
    
    # Resource name (e.g., "Room 305", "4K Projector")
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="A unique, identifiable name for the resource."
    )
    
    # Detailed description of the resource
    description = models.TextField(
        blank=True,
        help_text="Detailed information about the resource (features, location, etc.)."
    )
    
    # Resource type using defined choices
    type = models.CharField(
        max_length=5,
        choices=RESOURCE_CHOICES,
        default='OTHER',
        help_text="The category of the resource (e.g., Room, Equipment)."
    )
    
    # Maximum capacity (e.g., number of seats in a room, or 1 for equipment)
    capacity = models.IntegerField(
        default=1,
        help_text="The maximum number of people or concurrent uses allowed."
    )

    # --- 3. Implement __str__ method ---
    def __str__(self):
        """
        Returns a string representation of the model instance, 
        useful for the Django Admin and debugging.
        """
        return f"{self.name} ({self.get_type_display()})"

    # --- 4. Define Meta Class (Optional but Recommended) ---
    class Meta:
        verbose_name = "Bookable Resource"
        verbose_name_plural = "Bookable Resources"
        ordering = ['name']