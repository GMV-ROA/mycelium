function setCameraMode(mode) {
    var xhr = new XMLHttpRequest();    
    url = '/camera/set-mode/'+mode
    xhr.open('GET', url, true);
    xhr.send();
}

function toggleFrameSave(frame) {
    var xhr = new XMLHttpRequest();    
    url = '/camera/toggle-frame-save/'+frame
    xhr.open('GET', url, true);
    xhr.send();
}

function displayToggle() {
    display = !display

    if (display) {
        getImage('rgb')
    }
}

var display = false

function getImage(type) {
    if (!display) {
        document.getElementById("displayStatus").innerHTML = 'OFF'
        return
    }

    document.getElementById("displayStatus").innerHTML = 'ON'
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var img = this.responseText;
            document.getElementById(type+"_img").src = "data:image/png;base64,"+img;
        }    
    };
    
    xhr.open('GET', '/camera/get-latest-image/'+type, true);
    xhr.send();
}

setInterval(function() { getImage('rgb'); }, 1000);
// setInterval(function() { getImage('depth'); }, 5000);

// grab latest image filename
// then grab the image data with filename