//
// cromulent coffee javascript
//
// originally hosted at https://github.com/cromulentcoffee
//

var map;

function geo_loaded(result)
{
    // Load a GeoJSON from the same server as our demo.

    console.log("loading geo")
    
    map.data.addGeoJson(result)

    map.data.setStyle(style_feature);
}

function style_feature(feature)
{
	var name = feature.getProperty('name');
	var rating = feature.getProperty('rating');

	switch(rating) {
	case "cromulent":
		icon = "red-dot.png"
		break;
	case "insta-find":
		icon = "blue-dot.png"
		break;
	case "unverified":
	default:
		icon = "grey-dot.png"	
	}

	return {
	clickable: true,
			title: name,
			icon: icon

			};
}

// manage click events
infoWindow = new google.maps.InfoWindow({
    content: ""
});

// show an infowindow on click of a map pin
function click_event(event)
{

    // Main name and location
    info = '<div style="font-size: 16;"><b>' + event.feature.getProperty("name") + "</b></div>";

    if (typeof event.feature.getProperty('location') != 'undefined')
	info += '<div style="font-size: 12;"><b>' + event.feature.getProperty("location") + "</b></div>";

    // Rating
    info += '<div style="font-size: 12; color = #CCC;">';
    info += event.feature.getProperty("rating");
    info += '</div>';

    // Optional food and notes
    info += '<div style="font-size: 12;">';
    if (typeof event.feature.getProperty('food') != 'undefined')
	info += "<br />food: " + event.feature.getProperty("food");
    if (typeof event.feature.getProperty('notes') != 'undefined')
	info += "<br />" + event.feature.getProperty("notes");
    info += '</div>';

    // whitespace
    info += '<br />';

    // the set of badges
    info += '<div style="float: center; vertical-align: middle;">';

    // homepage
    if (typeof event.feature.getProperty('url') != 'undefined')
	info += "<a href=" + event.feature.getProperty("url") + '><img src="home.png" /></a>';

    // yelp
    if (typeof event.feature.getProperty('yelp') != 'undefined')
	info += "<a href=" + event.feature.getProperty("yelp") + '><img src="yelp.png" /></a>';

    // instagram
    if (typeof event.feature.getProperty('ig') != 'undefined')
	info += '<a href="http://instagram.com/' + event.feature.getProperty("ig") + '?ref=badge"><img src="http://badges.instagram.com/static/images/ig-badge-24.png" alt="Instagram" /></a>';

    // twitter
    if (typeof event.feature.getProperty('twitter') != 'undefined')
	info += '<a href="http://twitter.com/' + event.feature.getProperty("twitter") + '"><img src="twitter.png" alt="Twitter" /></a>';

    // google maps link
    var lllit = event.feature.getGeometry().get();
    qstr = lllit.lat() + "," + lllit.lng();
	
    info += '<a href="http://maps.google.com/?q=' + qstr + '"><img src="maps.png" alt="Maps" /></a>';
    info += "</div>";

    // and the insta pic
    if (typeof event.feature.getProperty('igpost') != 'undefined') {
	var p = event.feature.getProperty('igpost');
	var link = p["url"];
	var timg = p["thumb"]["url"];
	var w = p["thumb"]["width"];
	var h = p["thumb"]["height"];

	info += "<br />"
	info += '<a href="' + link + '"><img src="' + timg + '" with="' + w + 'px" height="' + h + 'px" /></a>'
    }
    

    // set it up
    infoWindow.setContent(info);
    
    var anchor = new google.maps.MVCObject();
    anchor.set("position",event.latLng);
    anchor.set("anchorPoint", new google.maps.Point(0,-40));
    infoWindow.open(map,anchor);
}


// functions to handle setting locations
var mapOptionsSF = {
    center: new google.maps.LatLng(37.7933, -122.4167),
    zoom: 12
}

function map_align_sf()
{
    console.log("align sf");
    map.panTo(mapOptionsSF['center']);
    map.setZoom(mapOptionsSF['zoom']);
}

function map_align_ca()
{
    console.log("align ca");
    map.panTo(new google.maps.LatLng(37.7833, -122.4167));
    map.setZoom(6);
}

function map_align_world()
{
    map.panTo(new google.maps.LatLng(0,0));
    map.setZoom(2);
}

function getURLParameter(name) {
    // unashamedly stolen from stackoverflow
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null
}

function get_init_map_position()
{
    // default to SF
    var lat = mapOptionsSF.center.lat();
    var lng = mapOptionsSF.center.lng();
    var zoom = mapOptionsSF.zoom;
    
    // check for URL parameters
    ulat = getURLParameter("lat");
    ulng = getURLParameter("lng");
    uzoom = getURLParameter("zoom");

    ulat = parseFloat(ulat);
    ulng = parseFloat(ulng);
    uzoom = parseFloat(uzoom);
    
    console.log("ulat: " + ulat)
    console.log("ulng: " + ulng)
    console.log("uzoom: " + uzoom)

    if (!isNaN(ulat))
	lat = ulat;

    if (!isNaN(ulng))
	lng = ulng;

    if (!isNaN(uzoom))
	zoom = uzoom;

    console.log("lat: " + lat)
    console.log("lng: " + lng)
    console.log("zoom: " + zoom)
    

    return {
	center: new google.maps.LatLng(lat, lng),
	zoom: zoom
    }
}

function maps_init()
{
    var mapCanvas = document.getElementById('map-canvas');

    map = new google.maps.Map(mapCanvas, get_init_map_position());

    //listen for click events
    map.data.addListener('click', click_event);

    console.log("geting json");
    jQuery.getJSON("ccgeo.json", "", geo_loaded);
    console.log("got json");

}

function cc_init()
{
    maps_init();

    // Hook the location links
    document.getElementById('map-sf').addEventListener('click',
						       map_align_sf, false);
    document.getElementById('map-ca').addEventListener('click',
						       map_align_ca, false);
    document.getElementById('map-world').addEventListener('click',
							  map_align_world, false);
}

// Predicate everything on the load even
google.maps.event.addDomListener(window, 'load', cc_init);

