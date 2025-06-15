# core/widgets.py
from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe

class NepaliDatePickerWidget(TextInput):
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/nepali-datepicker@4.0.0/nepali.datepicker.v4.0.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/npm/nepali-datepicker@4.0.0/nepali.datepicker.v4.0.min.js',
        )

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        js = f'''
        <script type="text/javascript">
        document.addEventListener("DOMContentLoaded", function () {{
            var input = document.getElementById("id_{name}");
            if (input && typeof input.nepaliDatePicker === "function") {{
                input.nepaliDatePicker({{
                    ndpYear: true,
                    ndpMonth: true,
                    ndpYearCount: 100
                }});
            }}
        }});
        </script>
        '''
        return mark_safe(html + js)
