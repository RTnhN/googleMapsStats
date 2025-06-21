let selectedGps = null;
const pairs = {};

fetch('/api/images')
  .then(r => r.json())
  .then(({gps, other}) => {
    const g = document.getElementById('gps');
    gps.forEach(url => {
      const img = document.createElement('img');
      img.src = url;
      img.onclick = () => {
        if (selectedGps) selectedGps.classList.remove('selected');
        selectedGps = img;
        img.classList.add('selected');
      };
      g.appendChild(img);
    });
    const o = document.getElementById('other');
    other.forEach(url => {
      const img = document.createElement('img');
      img.src = url;
      img.onclick = () => {
        if (!selectedGps) return alert('Select a GPS first');
        pairs[selectedGps.src] = url;
        // hide paired images
        selectedGps.style.display = 'none';
        img.style.display = 'none';
        selectedGps.classList.remove('selected');
        selectedGps = null;
        showPairs();
      };
      o.appendChild(img);
    });
  });

function showPairs() {
  document.getElementById('pairs').textContent = JSON.stringify(pairs, null, 2);
}


