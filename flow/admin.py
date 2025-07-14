from django.contrib import admin
from .models import FAQCategory, FAQ

@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'faq_count', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']

    def faq_count(self, obj):
        return obj.faqs.filter(is_active=True).count()
    faq_count.short_description = 'Active FAQs'

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'category', 'order', 'views', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['category__order', 'order', 'question']
    raw_id_fields = ['created_by']

    def question_short(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_short.short_description = 'Question'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new FAQ
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
# Register your models here.
