# apps/assessments/api/views.py
from rest_framework import viewsets, permissions
from ..models import IRO
from .serializers import IROSerializer
from ..views import ContextMixin  # Import the ContextMixin

class IROViewSet(ContextMixin, viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing IRO instances.
    """
    queryset = IRO.objects.all()
    serializer_class = IROSerializer
    permission_classes = [permissions.IsAuthenticated]  # ensure only authenticated users