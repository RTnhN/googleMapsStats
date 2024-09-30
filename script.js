//Make sure to make this one line before using it
// https://codebeautify.org/multiline-to-single-line
javascript:(function() {
    // Return early if not on the correct URL

    if (!window.location.href.startsWith('https://www.google.com/maps/contrib')) {
        alert('This script only works on https://www.google.com/maps/contrib');
        return;
    }

    let buttons = document.querySelectorAll('button');
    let imageData = [];

    buttons.forEach(button => {
        let imgDiv = button.querySelector('div:nth-child(1) > img[decoding]');
        let viewCountDiv = button.querySelector('div:nth-child(2) > div');

        if (imgDiv) {
            let imgSrc = imgDiv.src;
            let viewCount = 0;
            if (viewCountDiv) {
                viewCount = Number(viewCountDiv.textContent.trim().replaceAll(',', ''));
            }
            imageData.push({
                imageUrl: imgSrc,
                views: viewCount
            });
        }
    });

    function convertToCSV(data) {
        const header = ["Image URL", "View Count"];
        const csvRows = [header.join(",")];
        data.forEach(row => {
            csvRows.push([row.imageUrl, row.views].join(","));
        });
        return csvRows.join("\n");
    }

    function downloadCSV(data) {
        const csvData = convertToCSV(data);
        const blob = new Blob([csvData], { type: 'text/csv' });

        // Get the current date and time, including hours, minutes, and seconds
        const today = new Date();
        const dateString = today.toISOString().split('T')[0];
        const timeString = `${today.getHours()}-${today.getMinutes()}-${today.getSeconds()}`;
        const filename = `image_data_${dateString}_${timeString}.csv`;

        const url = window.URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.setAttribute('href', url);
        a.setAttribute('download', filename);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    downloadCSV(imageData);

})();
