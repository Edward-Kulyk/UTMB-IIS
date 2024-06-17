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

// Function to get default values based on campaign name
function getDefaultValues(campaignName) {
    fetch(`/get_default_values/${campaignName}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        // Setting default values
        document.getElementById("url").value = data.url_by_default;
        document.getElementById("domain").value = data.domain_by_default;
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Handler for campaign name selection
document.getElementById("campaign_name").addEventListener('change', function() {
    var selectedCampaign = this.value;
    getDefaultValues(selectedCampaign);
});

// Form submission handler
document.querySelector('form').addEventListener('submit', function (e) {
    var url = document.getElementById('url');
    var urlOther = document.getElementById('url_other');
    if (url.value === 'other') {
        url.value = urlOther.value;
    }

    var campaignName = document.getElementById('campaign_name');
    var campaignNameOther = document.getElementById('campaign_name_other');
    if (campaignName.value === 'other') {
        campaignName.value = campaignNameOther.value;
    }

    var campaignSource = document.getElementById('campaign_source');
    var campaignSourceOther = document.getElementById('campaign_source_other');
    if (campaignSource.value === 'other') {
        campaignSource.value = campaignSourceOther.value;
    }

    var campaignMedium = document.getElementById('campaign_medium');
    var campaignMediumOther = document.getElementById('campaign_medium_other');
    if (campaignMedium.value === 'other') {
        campaignMedium.value = campaignMediumOther.value;
    }

    var campaignContent = document.getElementById('campaign_content');
    var campaignContentOther = document.getElementById('campaign_content_other');
    if (campaignContent.value === 'other') {
        campaignContent.value = campaignContentOther.value;
    }
});
