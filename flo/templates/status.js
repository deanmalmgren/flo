var width = 960;
var height = 500;
var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

// there isn't a default DAG layout in d3 yet, not that I've
// necessarily seen any good algorithms for doing on the issue that's
// tracking it https://github.com/mbostock/d3/issues/349
//
// for now, use a force directed layout
// http://bl.ocks.org/mbostock/4062045
var force = d3.layout.force()
    .charge(-120)
    .linkDistance(40)
    .size([width, height])
    .nodes(document.graph.nodes)
    .links(document.graph.links)
    .start();

var link = svg.selectAll(".link")
    .data(document.graph.links)
    .enter()
    .append("line")
    .attr("class", "link")
    .style("stroke-width", 3);

var node = svg.selectAll(".node")
    .data(document.graph.nodes)
    .enter()
    .append("circle")
    .attr("class", function (d) { 
	if (d.in_sync) 
	    return "node synced";
	return "node not_synced"
    })
    .attr("r", 10)
    .call(force.drag);

node.append("title")
    .text(function(d) { return d.task_id; });

force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
});

// add a color legend
var legend = svg.selectAll("g.color_legend")
    .data(["synced", "not_synced"])
    .enter()
    .append("g")
    .attr("class", "color_legend");
legend.each(function (d, i) {
    d3.select(this)
	.append("rect")
	.attr("x", 10)
	.attr("y", i*16 + 10*(i+1))
	.attr("height", 16)
	.attr("width", 16)
	.attr("class", d);
    d3.select(this)
	.append("text")
	.attr("x", 10*2+16)
	.attr("y", (i+0.5)*16 + 10*(i+1))
	.attr("dy", "0.35em")
	.text(d);
})
