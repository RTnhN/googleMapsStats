javascript:(async function() {
    const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

    if (!window.location.href.startsWith('https://www.google.com/maps/contrib')) {
        alert('This script only works on https://www.google.com/maps/contrib');
        return;
    }

    let buttons = document.querySelectorAll('button');
    let imageData = [];

    for (let button of buttons) {
        let imgDiv = button.querySelector('div:nth-child(1) > img[decoding]');
        let viewCountDiv = button.querySelector('div:nth-child(2) > div');
        if (imgDiv) {
            button.click();
            await sleep(100); 

            let allDivs = document.querySelectorAll('div');
            let captureDate = 'Unknown'; 

            allDivs.forEach(div => {
                if (div.textContent.includes("Image capture:")) {
                    let text = div.textContent;
                    let dateMatch = text.match(/Image capture: (\w+ \d{4})/); 
                    if (dateMatch && dateMatch[1]) {
                        captureDate = dateMatch[1];
                    }
                }
            });

            let imgSrc = imgDiv.src;
            let viewCount = 0;
            if (viewCountDiv) {
                viewCount = Number(viewCountDiv.textContent.trim().replaceAll(',', ''));
            }
            imageData.push({
                imageUrl: imgSrc,
                views: viewCount, 
                postDate: captureDate
            });
        }
    }

    function convertToCSV(data) {
        const header = ["Image URL", "View Count", "Image Capture Date"];
        const csvRows = [header.join(",")];
        data.forEach(row => {
            csvRows.push([row.imageUrl, row.views, row.postDate].join(","));
        });
        return csvRows.join("\n");
    }

    function downloadCSV(data) {
        const csvData = convertToCSV(data);
        const blob = new Blob([csvData], { type: 'text/csv' });

        const today = new Date();
        const dateString = today.toISOString().replace(/:/g, '_');

        const filename = `imageData+${dateString}.csv`;

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
