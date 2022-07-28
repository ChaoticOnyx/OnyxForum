function UploadFile(endpoint_url, csrf_token) {
    var fileElement = document.getElementById('fileupload')
      // check if user had selected a file
    if (fileElement.files.length === 0) {
        alert('Please choose some files')
        return
    }

    var files = Array.from(fileElement.files)

    var formData = new FormData();
    files.forEach(function (file) {
        formData.append('file', file);
    });
    formData.append('csrf_token', csrf_token)

    $.ajax({
    url: endpoint_url,
    type: "POST",
    data:formData,
    contentType: false,
    processData: false,
    success: HandleResult
    });
};

function HandleResult(data) {
    var defaultbar = document.getElementById(".default")
    var errorbars = document.querySelectorAll('span [id="error"]')
    errorbars.forEach(function(errorbar) {
        errorbar.hide()
    });
    if(data.includes("/uploads?file=")){
        defaultbar.show()
        return document.location.origin+data
    }else{
        defaultbar.hide()
        errorbars.getElementById(data).show()
        console.log(data)
        return document.location.origin+data
    }
};

function UploadAvatar(endpoint_url, csrf_token) {
    var fileElement = document.getElementById('fileupload')
      // check if user had selected a file
    if (fileElement.files.length === 0) {
        alert('Please choose some files')
        return
    }

    var files = Array.from(fileElement.files)

    var formData = new FormData();
    files.forEach(function (file) {
        formData.append('file', file);
    });
    formData.append('csrf_token', csrf_token)

    $.ajax({
    url: endpoint_url,
    type: "POST",
    data:formData,
    contentType: false,
    processData: false,
    success: function(data){
        HandleResult(data)
        console.log(data)
        document.querySelector('input[name="avatar"]').value = document.location.origin+data;
        document.querySelector('img[name="avatar"]').src = document.location.origin+data;
    }
    });
    
};