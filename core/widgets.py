# core/widgets.py
from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe

class NepaliDatePickerWidget(TextInput):
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/nepali-datepicker-reactjs/dist/index.css',)
        }
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://cdn.jsdelivr.net/npm/nepali-datepicker-reactjs/dist/index.js',
        )

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        js = f'''
        <script>
        (function($) {{
            $(document).ready(function() {{
                $('#id_{name}').nepaliDatePicker({{
                    ndpYear: true,
                    ndpMonth: true,
                    ndpYearCount: 100,
                }});
            }});
        }})(django.jQuery);
        </script>
        '''
        return mark_safe(html + js)
