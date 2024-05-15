document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const openBtn = document.querySelector('.open-btn');
    const closeBtn = document.querySelector('.close-btn');
    const content = document.querySelector('.content');
    console.log("xuj");
    openBtn.addEventListener('click', function() {
        sidebar.style.width = '250px';
        content.style.marginLeft = '250px';
    });

    closeBtn.addEventListener('click', function() {
        sidebar.style.width = '0';
        content.style.marginLeft = '0';
    });
});