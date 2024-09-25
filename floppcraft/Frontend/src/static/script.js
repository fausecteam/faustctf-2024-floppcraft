var dataForm = document.getElementById("dataForm");

if (dataForm != null){
    dataForm.addEventListener("submit", function(e) {
        var formData = new FormData(dataForm);
        //var xml = '<?xml version="1.0" encoding="UTF-8"?>';
        var xml = '<!DOCTYPE dataRoot SYSTEM "/src/static/' + formData.get("formType") +'.dtd">'
        xml += "<dataRoot>";
        for(var entry of formData.entries()){
            var name = entry[0];
            var value = entry[1];
            console.log(name + ":" + value);
            xml += "<" + name + ">" + value + "</"+name+">";
            for(var elem of document.getElementsByName(name)){
                elem.removeAttribute("name");
            }
        }
        xml += "</dataRoot>";
        var newElem = document.createElement("input");
        newElem.setAttribute("type","hidden");
        newElem.setAttribute("name","xmlData");
        newElem.setAttribute("value",xml);
        dataForm.appendChild(newElem);
    });
}
