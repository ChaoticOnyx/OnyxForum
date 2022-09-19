function UploadFile(endpoint_url, csrf_token, uploaded_file, callback) {
    var file = null
    var formData = new FormData();
    if(!uploaded_file){
        var fileElement = document.getElementById('fileupload')
        // check if user had selected a file
        if (fileElement.files.length === 0) {
            alert('Please choose some files')
            return
        }
        file = fileElement.files[0]
    }else{
        file = uploaded_file
    }
    formData.append('file', file);

    formData.append('csrf_token', csrf_token)
    var link = [file.type]
    $.ajax({
        url: endpoint_url,
        type: "POST",
        data:formData,
        contentType: false,
        processData: false,
        success: function(data){
            if(HandleResult(data)){
                link.push(document.location.origin+data)
                callback(link[0],link[1])
            }
        }
    })
    
    
};

function HandleResult(data) {
    var defaultbar = document.querySelector('label.filestatus span[id="error none"]')
    var errorbars = document.querySelectorAll('label.filestatus span')
    errorbars.forEach(function(errorbar) {
        errorbar.style.display = "none";
    });
    if(data.includes("/uploads?file=")){
        defaultbar.style.display = "inline-block";
        return true
    }else{
        defaultbar.style.display = "none";
        document.getElementById("error "+data).style.display = "inline-block";
        return false
    }
};

function UploadAvatar(endpoint_url, csrf_token) {
    var fileElement = document.getElementById('fileupload')
      // check if user had selected a file
    if (fileElement.files.length === 0) {
        alert('Please choose some files')
        return
    }

    var file = fileElement.files[0]
    if(!file.type.includes("image"))
        return HandleResult('bad-file')

    resize(file, file.type).then(function(temp_file){
        var formData = new FormData();
        formData.append('file', dataURLtoFile(temp_file[0],temp_file[1]))
        formData.append('csrf_token', csrf_token)
        $.ajax({
        url: endpoint_url,
        type: "POST",
        data:formData,
        contentType: false,
        processData: false,
        success: function(data){
            if(HandleResult(data)){
                document.querySelector('input[name="avatar"]').value = document.location.origin+data;
                document.querySelector('img[name="avatar"]').src = document.location.origin+data;
            }
        }
        });
    
    })
    };

function resize(item, item_type, width){
    //define the width to resize e.g 150px
    var resize_width=width||150;
    //create a FileReader
    var reader = new FileReader();
  
    //image turned to base64-encoded Data URI.
    reader.readAsDataURL(item);
    reader.name = item.name;//get the image's name
    reader.size = item.size; //get the image's size
    return new Promise(function(resolve, reject) {
        reader.onload = function(event) {
            var img = new Image();//create a image
            img.src = event.target.result;//result is base64-encoded Data URI
            img.name = event.target.name;//set name (optional)
            img.size = event.target.size;//set size (optional)
            img.onload = function(el) {
              var elem = document.createElement('canvas');//create a canvas
            
              elem.width = el.target.width
              elem.height = el.target.height
              //scale the image to 150 (width) and keep aspect ratio
              if(el.target.width>resize_width){
              var scaleFactor = resize_width / el.target.width;
              elem.width = resize_width;
              elem.height = el.target.height * scaleFactor;
            }
        
              //draw in canvas
              var ctx = elem.getContext('2d');
              ctx.drawImage(el.target, 0, 0, elem.width, elem.height);
        
              //get the base64-encoded Data URI from the resize image
              var srcEncoded = ctx.canvas.toDataURL(item_type, 1);
              resolve([srcEncoded, el.target.name])
              /*Now you can send "srcEncoded" to the server and
              convert it to a png o jpg. Also can send
              "el.target.name" that is the file's name.*/
        
            }
          }
    })
  }

function dataURLtoFile(dataurl, filename) {
    var arr = dataurl.split(','),
        mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[1]), 
        n = bstr.length, 
        u8arr = new Uint8Array(n);
        
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    
    return new File([u8arr], filename, {type:mime});
}

function dropHandler(ev, endpoint_url, csrf_token) {
    // Prevent default behavior (Prevent file from being opened)
    ev.preventDefault();
    if (ev.dataTransfer.items) {
      // Use DataTransferItemList interface to access the file(s)
      for (var i = 0; i < ev.dataTransfer.items.length; i++) {
        // If dropped items aren't files, reject them
        if (ev.dataTransfer.items[i].kind === 'file') {
          var file = ev.dataTransfer.items[i].getAsFile();
         UploadFile(endpoint_url, csrf_token, file,file_link_append)
        }
      }
    } else {
      // Use DataTransfer interface to access the file(s)
      for (var i = 0; i < ev.dataTransfer.files.length; i++) {
        UploadFile(endpoint_url, csrf_token, ev.dataTransfer.files[i],file_link_append)
      }
    }
}

function dragOverHandler(ev) {
    ev.preventDefault();
}

function filestatus_click_handler(endpoint_url, csrf_token) {
    var fileElement = document.getElementById('fileupload')
        // check if user had selected a file
        if (fileElement.files.length === 0) {
            alert('Please choose some files')
            return
        }
        file = fileElement.files[0]
    UploadFile(endpoint_url, csrf_token, file, file_link_append)
}

function file_link_append(file_type, file_link){
    if(file_link)
        if(file_type.includes("image")){
            document.querySelector('textarea').value += '\n![enter image description here]('+file_link+' "enter image title here")'
        }else{
            document.querySelector('textarea').value += '\n[enter link description here]('+file_link+')'
        }
}
