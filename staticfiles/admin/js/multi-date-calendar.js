(function($) {
    // Kalendar uchun yordamchi funksiyalar
    window.MultiDateCalendar = {
        // Sanalarni eksport qilish
        exportDates: function(widgetId) {
            var dates = $('#' + widgetId).val().split(',').filter(function(date) {
                return date.trim() !== '';
            });
            return dates;
        },

        // Sanalarni import qilish
        importDates: function(widgetId, dates) {
            $('#' + widgetId).val(dates.join(','));
            $('#calendar-' + widgetId).datepicker('refresh');
        },

        // Sanalar orasidagi kunlarni hisoblash
        getDaysCount: function(widgetId) {
            var dates = this.exportDates(widgetId);
            return dates.length;
        }
    };
})(django.jQuery);