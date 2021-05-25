var service = 'mav_router'
var lines = 20

function getLog() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            var log = document.getElementById("logBox")
            log.innerHTML = data.join("<br>")
            document.getElementById("serviceTitle").innerHTML = service
        }
    
    };
    
    xhr.open('GET', '/service/log/'+service+'/'+lines, true);
    xhr.send();
}

setInterval(getLog, 500);

function switchService(sv) {
    service = sv
}

function setLines(li) {
    lines = li
}