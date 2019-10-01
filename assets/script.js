var html = document.getElementsByTagName("html")[0];
if(html.classList.contains("apple_client-application")){
    if(!html.classList.contains("apple_display-separateview")){
        html.classList.add("apple_client-spotlight");
    }
}