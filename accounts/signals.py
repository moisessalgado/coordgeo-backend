from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import User


@receiver(post_save, sender=User)
def create_personal_organization(sender, instance, created, **kwargs):
    """
    Cria automaticamente uma organização PERSONAL para novos usuários.
    
    Esta organização:
    - É do tipo PERSONAL
    - Tem plano FREE por padrão, ou PRO quando selecionado no signup
    - É invisível para usuários freemium no frontend (não aparece na lista)
    - Serve como workspace padrão do usuário
    """
    if created:
        from organizations.models import Organization, Membership
        selected_plan = getattr(instance, '_selected_signup_plan', Organization.Plan.FREE)

        # Keep signup scope limited to free/pro for now.
        if selected_plan not in [Organization.Plan.FREE, Organization.Plan.PRO]:
            selected_plan = Organization.Plan.FREE
        
        # Criar organização pessoal
        base_slug = slugify(instance.email.split('@')[0])
        slug = base_slug
        counter = 1
        
        # Garantir slug único
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        org = Organization.objects.create(
            name=f"Workspace de {instance.email}",
            slug=slug,
            description="Organização pessoal",
            org_type=Organization.OrgType.PERSONAL,
            plan=selected_plan,
            owner=instance
        )
        
        # Criar membership automático como admin
        Membership.objects.create(
            user=instance,
            organization=org,
            role=Membership.Role.ADMIN
        )
