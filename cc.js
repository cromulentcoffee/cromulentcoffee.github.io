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

var locations = {

    "world": [ "world",
		new google.maps.LatLng(-58.631217, -18.105469),
		new google.maps.LatLng(72.289067, -15.644531) ],
    
    "usa": [ "USA",
	     new google.maps.LatLng(23.079732, -125.419922),
	     new google.maps.LatLng(52.052490, -58.974609) ],

    "CA": [ "  California",
	    new google.maps.LatLng(32.398516, -123.991699),
	    new google.maps.LatLng(42.228517, -115.202637) ],

    "sfbay": [ "    Bay Area",
	       new google.maps.LatLng(37.317752, -122.471466),
	       new google.maps.LatLng(38.032949, -122.045746) ],
    
    "SF": [ "    San Francsico",
	    new google.maps.LatLng(37.732168, -122.538414),
	    new google.maps.LatLng(37.869433, -122.254143) ],

    "PacNW": [ "  Pacific NW",
	       new google.maps.LatLng(41.672912, -124.694824),
	       new google.maps.LatLng(49.181703, -116.169434) ],
    
    "asia": [ "Asia",
	      new google.maps.LatLng(-17.811456, 88.154297),
	      new google.maps.LatLng(47.754098, 148.974609) ],

    "seoul": [ "Seoul",
	       new google.maps.LatLng(37.498831, 126.926594),
	       new google.maps.LatLng(37.576964, 127.040577) ],

    "HK": [ "Hong Kong",
	    new google.maps.LatLng(22.197577, 114.096794),
	    new google.maps.LatLng(22.339914, 114.281502) ],

    "AU": [ "Australia",
	    new google.maps.LatLng(-44.964798, 112.236328),
	    new google.maps.LatLng(-8.928487, -174.990234) ],

    "EU": [ "Europe",
	    new google.maps.LatLng(35.460670, -10.634766),
	    new google.maps.LatLng(68.528235, 36.826172) ]
};

function set_location(loc)
{
    map.fitBounds(new google.maps.LatLngBounds(loc[1], loc[2]));
}

function location_select()
{
    var llist = document.getElementById('location');
    loc = locations[llist.value]
    console.log("lol " + loc[0] );

    set_location(loc)
}

function fill_locations()
{
    var llist = document.getElementById('location');

    //llist.options.add(new Option("SF", "sf"));

    for (var k in locations) {
	var d = locations[k];
	llist.options.add(new Option(d[0], k));
    }
    
    // setup for clicking
    llist.addEventListener('click',
			   location_select, false);
}

function getURLParameter(name) {
    // unashamedly stolen from stackoverflow
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null
}

function get_init_map_position()
{
    // fill out the location selector
    fill_locations();
    
    return {
	center: new google.maps.LatLng(0, 0),
	zoom: 4
    }
}

function set_init_map_position()
{
    locname = getURLParameter("loc");

    if (locname == null)
	locname = "world";

    if (!(locname in locations))
	locname = "world";
    
    loc = locations[locname];
    set_location(loc);

    // set the drop-down, too!
    var llist = document.getElementById('location');
    llist.value = locname;
}

function maps_init()
{
    var mapCanvas = document.getElementById('map-canvas');

    map = new google.maps.Map(mapCanvas, get_init_map_position());

    // set the bounds
    set_init_map_position();

    
    //listen for click events
    map.data.addListener('click', click_event);

    console.log("geting json");
    jQuery.getJSON("ccgeo.json", "", geo_loaded);
    console.log("got json");

}

function cc_init()
{
    maps_init();
}

// Predicate everything on the load even
google.maps.event.addDomListener(window, 'load', cc_init);

