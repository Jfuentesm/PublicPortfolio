<!-- src/frontend/src/components/CanvasView.vue -->
<template>
    <div class="canvas-view">
        <h2>Infinite Canvas</h2>
        <!-- Container for D3.js rendered canvas -->
        <div ref="canvasContainer" class="canvas-container"></div>
    </div>
  </template>
  
  <script>
  import * as d3 from 'd3'
  
  /**
   * CanvasView.vue
   *
   * A component that implements an infinite canvas using D3.js.
   * Users can pan and zoom to explore the canvas.
   * Nodes and edges can be added for visual note/task layout.
   */
  export default {
    name: 'CanvasView',
    data() {
        return {
            svg: null,     // D3 selection for the SVG element
            svgGroup: null // D3 group element inside SVG for panning and zooming
        }
    },
    mounted() {
        this.initCanvas()
    },
    methods: {
        /**
         * Initializes the infinite canvas using D3.js.
         * Sets up the SVG element, zoom behavior, and adds sample nodes.
         */
        initCanvas() {
            // Reference to the canvas container DOM element
            const container = this.$refs.canvasContainer
  
            // Create an SVG element that fills the container
            this.svg = d3.select(container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
  
            // Append a group element for panning and zooming
            this.svgGroup = this.svg.append('g')
  
            // Define zoom behavior with scale limits
            const zoomBehavior = d3.zoom()
                .scaleExtent([0.5, 5])
                .on('zoom', (event) => {
                    // Apply transformation to the group element
                    this.svgGroup.attr('transform', event.transform)
                })
  
            // Apply the zoom behavior to the SVG element
            this.svg.call(zoomBehavior)
  
            // Add a sample node to demonstrate functionality
            this.addSampleNode(100, 100, 'Sample Node')
        },
  
        /**
         * Adds a sample node to the canvas for demonstration.
         *
         * @param {Number} cx - X-coordinate of the node center.
         * @param {Number} cy - Y-coordinate of the node center.
         * @param {String} label - Label text for the node.
         */
        addSampleNode(cx, cy, label) {
            // Create a group element for the node
            const nodeGroup = this.svgGroup.append('g')
                .attr('class', 'canvas-node')
                .attr('transform', `translate(${cx}, ${cy})`)
  
            // Append a circle to represent the node
            nodeGroup.append('circle')
                .attr('r', 30)
                .attr('fill', 'steelblue')
  
            // Append text to label the node
            nodeGroup.append('text')
                .attr('y', 5)
                .attr('text-anchor', 'middle')
                .attr('fill', '#fff')
                .text(label)
        }
    }
  }
  </script>
  
  <style scoped>
  .canvas-view {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .canvas-container {
    flex: 1;
    border: 1px solid #ccc;
    overflow: hidden;
    position: relative;
  }
  </style>
  