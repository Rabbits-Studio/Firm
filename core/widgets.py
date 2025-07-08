from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe

class NepaliUnicodeTextInput(TextInput):
    class Media:
        css = {
            'all': (
                # Optional: Load Devanagari fonts if needed
                # 'https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari&display=swap',
            )
        }

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['style'] = (
            'font-family: Kalimati, Mangal, "Noto Sans Devanagari", Arial, sans-serif; '
            'font-size: 14px;'
        )
        return super().render(name, value, attrs, renderer)


class NepaliDatePickerWidget(TextInput):
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/nepali-datepicker@4.0.0/nepali.datepicker.v4.0.min.css',
            )
        }
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://cdn.jsdelivr.net/npm/nepali-datepicker@4.0.0/nepali.datepicker.v4.0.min.js',
        )

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['class'] = (attrs.get('class', '') + ' nepali-datepicker').strip()

        html = super().render(name, value, attrs, renderer)
        js = f'''
        <script type="text/javascript">
        (function($) {{
            $(document).ready(function() {{
                $('input[name="{name}"]').nepaliDatePicker({{
                    ndpYear: true,
                    ndpMonth: true,
                    ndpYearCount: 100
                }});
            }});
        }})(window.jQuery || django.jQuery);
        </script>
        '''
        return mark_safe(html + js)
