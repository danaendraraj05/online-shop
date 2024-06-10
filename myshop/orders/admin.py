from django.contrib import admin
from .models import Order, OrderItem
import csv
import datetime
from django.http import HttpResponse
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html, mark_safe
from django.utils.safestring import mark_safe
from .views import admin_order_pdf  # Import the view function

def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]

    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])

    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)

    return response

export_to_csv.short_description = 'Export to CSV'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'paid', 'created', 'updated', 'view_order_detail', 'order_pdf']
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]
    actions = [export_to_csv]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:order_id>/detail/', self.admin_site.admin_view(self.order_detail), name='orders_order_detail'),
            path('<int:order_id>/pdf/', self.admin_site.admin_view(self.admin_order_pdf_view), name='orders_admin_order_pdf'),
        ]
        return custom_urls + urls

    def order_detail(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'admin/orders/order/detail.html', {'order': order})

    def view_order_detail(self, obj):
        return format_html('<a href="{}">View Order Detail</a>', reverse('admin:orders_order_detail', args=[obj.id]))
    view_order_detail.short_description = 'Order Detail'

    def order_pdf(self, obj):
        url = reverse('admin:orders_admin_order_pdf', args=[obj.id])
        return mark_safe(f'<a href="{url}">PDF</a>')
    order_pdf.short_description = 'Invoice'

    def admin_order_pdf_view(self, request, order_id):
        return admin_order_pdf(request, order_id)  # Call the function from views.py
