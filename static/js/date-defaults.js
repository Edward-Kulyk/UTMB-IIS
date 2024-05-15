document.addEventListener('DOMContentLoaded', function() {
    var date = new Date();
    var yesterday = new Date(date.getTime());
    yesterday.setDate(date.getDate() - 1);

    var dateStringToday = date.toISOString().split('T')[0];
    var dateStringYesterday = yesterday.toISOString().split('T')[0];

    document.getElementById('date_from').value = dateStringYesterday;
    document.getElementById('date_to').value = dateStringToday;
});
