(function () {
  'use strict'
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl)
  })
})()

function dark(){
    var main = document.getElementById('content-bg');
    main.style = "background-color:black;color:white;width: 100%;margin-left: 200px;margin-right: 0px;overflow:scroll;";
    alert("You have entered Dark mode(eperimental). Reload the page to return to Light Mode")
}

function togglesidebar(){
    var divider = document.getElementsByClassName('divider')[0];
    var main = document.getElementById('content-bg');
    var sidenav = document.getElementById('sidenav')

    if (divider.id === "sidebarexpanded"){
        main.style = "width: 100%;margin-right: 10px;overflow:scroll;";
        divider.style = "position:fixed;margin-right: 0px;";
        sidenav.style = "display:none;"
        divider.id = "sidebarhidden";
    }else if (divider.id === "sidebarhidden") {
        main.style = "width: 100%;margin-left: 200px;margin-right: 0px;overflow:scroll;";
        divider.style = "position:fixed;margin-left: 190px;";
        sidenav.style = "width: 190px;position: fixed;"
        divider.id = "sidebarexpanded";
    };
}
