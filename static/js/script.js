function toggleOtherInput(selectId, inputId) {
    var selectElement = document.getElementById(selectId);
    var inputElement = document.getElementById(inputId);

    if (selectElement.value === 'other') {
        inputElement.style.display = 'inline';
        inputElement.required = true;
    } else {
        inputElement.style.display = 'none';
        inputElement.required = false;
    }

    updateUtmLink();  // Call the function to update UTM link when the input changes
}

function updateUtmLink() {
    var url = getSelectedValue('url', 'url_other');
    var campaignContent = getSelectedValue('campaign_content', 'campaign_content_other');
    var campaignSource = getSelectedValue('campaign_source', 'campaign_source_other');
    var campaignMedium = getSelectedValue('campaign_medium', 'campaign_medium_other');
    var campaignName = getSelectedValue('campaign_name', 'campaign_name_other');
    var domain = document.getElementById('domain').value;
    var slug = document.getElementById('slug').value;

    // Construct the UTM link
     var dynamicUtmLink = `${url}?utm_campaign=${campaignName.replace(/ /g, '+')}&utm_medium=${campaignMedium.replace(/ /g, '+')}&utm_source=${campaignSource.replace(/ /g, '+')}&utm_content=${campaignContent.replace(/ /g, '+')}`;

    // Display the UTM link
    document.getElementById('utm-link').innerText = dynamicUtmLink;
}

function getSelectedValue(selectId, inputId) {
    var selectElement = document.getElementById(selectId);
    var inputElement = document.getElementById(inputId);

    if (selectElement.value === 'other') {
        return inputElement.value || 'other';
    } else {
        return selectElement.value;
    }
}

// Функция для отправки запроса на сервер и получения значений по умолчанию
function getDefaultValues(campaignName) {
    fetch('/get_default_values', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'campaign_name': campaignName }),
    })
    .then(response => response.json())
    .then(data => {
        // Установка полученных значений по умолчанию
        document.getElementById("url").value = data.url_by_default;
        document.getElementById("domain").value = data.domain_by_default;
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Обработчик выбора названия кампании
document.getElementById("campaign_name").addEventListener('change', function() {
    var selectedCampaign = this.value;
    getDefaultValues(selectedCampaign);
});