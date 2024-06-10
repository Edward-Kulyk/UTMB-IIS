    function toggleOtherInput(selectId, inputId) {
        const selectElement = document.getElementById(selectId);
        const inputElement = document.getElementById(inputId);
        if (selectElement.value === "other") {
            inputElement.style.display = "inline-block";
        } else {
            inputElement.style.display = "none";
        }
    }

    function getSelectedValue(selectId, inputId) {
        var selectElement = document.getElementById(selectId);
        var inputElement = document.getElementById(inputId);

        if (selectElement.value === 'other') {
            return inputElement.value || '';
        } else {
            return selectElement.value;
        }
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

    function prepareFormData(event) {
        event.preventDefault();

        // Update form values before submission
        updateSelectValue('url', 'url_other');
        updateSelectValue('campaign_name', 'campaign_name_other');
        updateSelectValue('campaign_source', 'campaign_source_other');
        updateSelectValue('campaign_medium', 'campaign_medium_other');
        updateSelectValue('campaign_content', 'campaign_content_other');

        // Remove "other" input fields before submitting the form
        document.getElementById('url_other').remove();
        document.getElementById('campaign_name_other').remove();
        document.getElementById('campaign_source_other').remove();
        document.getElementById('campaign_medium_other').remove();
        document.getElementById('campaign_content_other').remove();

        // Submit the form
        event.target.submit();
    }

    function updateSelectValue(selectId, inputId) {
        var selectElement = document.getElementById(selectId);
        var inputElement = document.getElementById(inputId);

        if (selectElement.value === 'other') {
            selectElement.value = inputElement.value;
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

