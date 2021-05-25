paginate = 20
database = 0

function getData() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;
    
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            html = generateDataBody(data)
            document.getElementById("dataBody").innerHTML = html
        }    
    };
    
    xhr.open('GET', '/redis/get-data/'+database+'/'+paginate, true);
    xhr.send();
}

function generateDataBody(data) {
    html = ''
    Object.keys(data).forEach(function(key) {
        val = JSON.stringify(data[key])
        row = '<tr> \
                <td>'+key+'</td> \
                <td>'+val+'</td> \
            </tr>'    
        html += row
    });
    return html    
}

function switchDatabase(db) {
    database = db
}

setInterval(getData, 1000);