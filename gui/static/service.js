function setServiceState(service, state) {
    var xhr = new XMLHttpRequest();    
    url = '/service/set-state/'+service+'/'+state
    xhr.open('GET', url, true);
    xhr.send();
}

function startAllServices() {
    var xhr = new XMLHttpRequest();    
    url = '/service/start-all'
    xhr.open('GET', url, true);
    xhr.send();
}

function stopAllServices() {
    var xhr = new XMLHttpRequest();    
    url = '/service/stop-all'
    xhr.open('GET', url, true);
    xhr.send();
}

function getStatus() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            var cells = document.getElementsByClassName("statusCell")
            for (i=0; i<cells.length; i++) {
                cells[i].innerHTML = data[i]
            }
        }
    
    };
    
    xhr.open('GET', '/service/status', true);
    xhr.send();
}

function getLog(lines) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            var cells = document.getElementsByClassName("output")
            for (i=0; i<cells.length; i++) {
                cells[i].innerHTML = data[i].join("<br>")
            }            
        }
    
    };
    
    xhr.open('GET', '/service/log-all/'+lines, true);
    xhr.send();
}

setInterval(getStatus, 3000);
setInterval(function() { getLog(5); }, 500);

function toggleDropdown(el) {
    var a = el.parentNode.nextElementSibling
    if (a.style.display == "none") {
        a.style.display = "table-row";
    } else {
        a.style.display = "none";
    }
}
