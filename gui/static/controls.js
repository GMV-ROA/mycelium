function getStatus() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            var cells = document.getElementsByClassName("statusCell")
            for (i=0; i<cells.length; i++) {
                if (parseInt(data[i] ) == 1) {
                    var status = "on"
                } else {
                    var status = "off"
                }
                cells[i].innerHTML = status
            }
        }
    
    };
    
    xhr.open('GET', '/controls/status-all', true);
    xhr.send();
}

setInterval(getStatus, 3000);

