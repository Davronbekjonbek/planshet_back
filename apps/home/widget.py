from django import forms
from django.utils.safestring import mark_safe


class MultiDateWidget(forms.Widget):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs['class'] = 'multi-date-picker'
        self.attrs = attrs

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs.update(self.attrs)

        widget_id = attrs.get('id', name)

        # Calendar HTML
        calendar_html = f'''
        <div class="multi-date-container">
            <input type="hidden" name="{name}" id="{widget_id}" value="{value or ""}" />

            <div style="display: flex; gap: 20px; margin: 10px 0; min-height: 300px;">
                <!-- Calendar qismi -->
                <div style="flex: 1; max-width: 350px;">
                    <div id="calendar-{widget_id}" style="background: white; border: 1px solid #ddd; border-radius: 4px;"></div>
                </div>

                <!-- Tanlangan sanalar qismi -->
                <div style="flex: 1; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px;">
                    <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 14px; color: #495057;">Tanlangan sanalar:</h4>
                    <div id="selected-dates-{widget_id}" style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; min-height: 40px;"></div>
                    <button type="button" id="clear-dates-{widget_id}" style="padding: 6px 12px; border: 1px solid #6c757d; border-radius: 4px; background: #6c757d; color: white; cursor: pointer; font-size: 12px;">
                        Hammasini tozalash
                    </button>
                </div>
            </div>
        </div>

        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/themes/ui-lightness/jquery-ui.min.css">

        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/jquery-ui.min.js"></script>

        <style>
        #{widget_id}-container .ui-datepicker {{
            font-size: 12px;
        }}

        #{widget_id}-container .ui-datepicker .ui-state-active {{
            background: #007bff !important;
            color: white !important;
            border-color: #007bff !important;
        }}

        #{widget_id}-container .selected-date-tag {{
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            display: inline-block;
            margin: 2px;
        }}

        #{widget_id}-container .remove-date {{
            margin-left: 5px;
            cursor: pointer;
            font-weight: bold;
        }}

        #{widget_id}-container .remove-date:hover {{
            color: #ff6b6b !important;
        }}
        </style>

        <script>
        (function() {{
            // jQuery mavjudligini tekshirish
            function waitForJQuery(callback) {{
                if (typeof jQuery !== 'undefined' && jQuery.ui && jQuery.ui.datepicker) {{
                    callback();
                }} else {{
                    setTimeout(function() {{ waitForJQuery(callback); }}, 100);
                }}
            }}

            waitForJQuery(function() {{
                var $ = jQuery;
                var widgetId = '{widget_id}';
                var calendar = $('#calendar-' + widgetId);
                var hiddenInput = $('#' + widgetId);
                var selectedDatesContainer = $('#selected-dates-' + widgetId);
                var selectedDates = [];

                // Agar kalendar allaqachon yaratilgan bo'lsa, uni yo'q qilish
                if (calendar.hasClass('hasDatepicker')) {{
                    calendar.datepicker('destroy');
                }}

                // Mavjud sanalarni yuklash
                var initialDates = hiddenInput.val();
                if (initialDates) {{
                    selectedDates = initialDates.split(',').filter(function(date) {{
                        return date.trim() !== '';
                    }});
                }}

                // Kalendar yaratish
                calendar.datepicker({{
                    dateFormat: 'yy-mm-dd',
                    showOtherMonths: true,
                    selectOtherMonths: true,
                    changeMonth: true,
                    changeYear: true,
                    showButtonPanel: true,
                    beforeShowDay: function(date) {{
                        var dateStr = $.datepicker.formatDate('yy-mm-dd', date);
                        var isSelected = selectedDates.indexOf(dateStr) !== -1;
                        return [true, isSelected ? 'ui-state-active' : '', isSelected ? 'Tanlangan' : ''];
                    }},
                    onSelect: function(dateText) {{
                        var index = selectedDates.indexOf(dateText);
                        if (index === -1) {{
                            // Sana qo'shish
                            selectedDates.push(dateText);
                        }} else {{
                            // Sanani olib tashlash
                            selectedDates.splice(index, 1);
                        }}
                        updateSelectedDates();
                        // Kalendarni yangilash
                        setTimeout(function() {{
                            calendar.datepicker('refresh');
                        }}, 10);
                    }}
                }});

                // Tanlangan sanalarni yangilash funksiyasi
                function updateSelectedDates() {{
                    selectedDates.sort();
                    hiddenInput.val(selectedDates.join(','));

                    var html = '';
                    selectedDates.forEach(function(date) {{
                        var formattedDate = formatDate(date);
                        html += '<span class="selected-date-tag">' + 
                               formattedDate + 
                               ' <span class="remove-date" data-date="' + date + '">×</span></span>';
                    }});

                    if (selectedDates.length === 0) {{
                        html = '<span style="color: #6c757d; font-style: italic;">Hech qanday sana tanlanmagan</span>';
                    }}

                    selectedDatesContainer.html(html);
                }}

                // Sanani formatlash
                function formatDate(dateStr) {{
                    try {{
                        var date = new Date(dateStr + 'T00:00:00');
                        var months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek'];
                        return date.getDate() + ' ' + months[date.getMonth()] + ' ' + date.getFullYear();
                    }} catch(e) {{
                        return dateStr;
                    }}
                }}

                // Sanani olib tashlash hodisasi
                selectedDatesContainer.on('click', '.remove-date', function() {{
                    var dateToRemove = $(this).data('date');
                    var index = selectedDates.indexOf(dateToRemove);
                    if (index !== -1) {{
                        selectedDates.splice(index, 1);
                        updateSelectedDates();
                        calendar.datepicker('refresh');
                    }}
                }});

                // Hammasini tozalash tugmasi
                $('#clear-dates-' + widgetId).click(function() {{
                    selectedDates = [];
                    updateSelectedDates();
                    calendar.datepicker('refresh');
                }});

                // Dastlabki ko'rinishni yangilash
                updateSelectedDates();

                console.log('Multi-date calendar initialized for:', widgetId);
            }});
        }})();
        </script>
        '''

        return mark_safe(calendar_html)

    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        if value:
            dates = [d.strip() for d in value.split(',') if d.strip()]
            return dates
        return []

    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, list):
            return ','.join([str(v) for v in value])
        return str(value)