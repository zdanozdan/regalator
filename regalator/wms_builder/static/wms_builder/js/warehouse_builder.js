/**
 * Warehouse Builder - Drag and Drop functionality
 */

class WarehouseBuilder {
    constructor(warehouseData = {}) {
        this.warehouseData = warehouseData || {};
        this.svg = null;
        this.currentZoom = 1;
        this.draggedElement = null;
        this.warehouseId = null;
        this.zoneMode = {
            activeZoneId: null,
            updateZonesVisibility: null,
            workspaceWidth: null,
            workspaceHeight: null
        };
        this.rackMode = {
            activeRackId: null
        };
        this.zoneModeSelect = null;
        this.detailBaseUrl = null;
    }

    init() {
        console.log('WarehouseBuilder.init() called');
        this.svg = document.getElementById('warehouse-svg');
        if (!this.svg) {
            console.error('SVG element not found!');
            return;
        }
        console.log('SVG element found:', this.svg);
        const viewBoxAttr = this.svg.getAttribute('viewBox');
        if (viewBoxAttr) {
            const parts = viewBoxAttr.split(' ').map(parseFloat);
            if (parts.length === 4) {
                this.zoneMode.workspaceWidth = parts[2] || null;
                this.zoneMode.workspaceHeight = parts[3] || null;
            }
        }
        if (!this.zoneMode.workspaceWidth || !this.zoneMode.workspaceHeight) {
            const bbox = this.svg.getBoundingClientRect();
            this.zoneMode.workspaceWidth = bbox.width || 1000;
            this.zoneMode.workspaceHeight = bbox.height || 800;
        }

        this.detailBaseUrl = this.svg.dataset && this.svg.dataset.detailBase ? this.svg.dataset.detailBase : null;
        const svgWarehouseId = this.svg.dataset && this.svg.dataset.warehouseId;
        if (svgWarehouseId) {
            this.warehouseId = parseInt(svgWarehouseId, 10);
        } else if (this.warehouseData && this.warehouseData.id) {
            this.warehouseId = this.warehouseData.id;
        }

        this.setupDragAndDrop();
        this.setupClickToEdit();
        this.setupContextMenu();
        this.setupZoomControls();
        this.setupZoneMode();
    }

    setupDragAndDrop() {
        // Make zones draggable
        interact('.draggable-zone')
            .draggable({
                preventDefault: 'auto',
                onstart: (event) => {
                    event.target.classList.add('dragging');
                },
                onmove: (event) => {
                    const target = event.target;
                    const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
                    
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);
                    
                    // Update the rect position (both x and y)
                    const rect = target.querySelector('.zone-rect');
                    if (rect) {
                        rect.setAttribute('x', x);
                        rect.setAttribute('y', y);
                    }
                    
                    // Update text position (center of rect)
                    const text = target.querySelector('text');
                    const width = parseFloat(target.getAttribute('data-width')) || 200;
                    const height = parseFloat(target.getAttribute('data-height')) || 150;
                    if (text) {
                        text.setAttribute('x', x + width / 2);
                        text.setAttribute('y', y + height / 2);
                    }
                    
                    // Update resize handle indicator position
                    const resizeHandle = target.querySelector('.resize-handle-indicator');
                    if (resizeHandle) {
                        resizeHandle.setAttribute('cx', x + width);
                        resizeHandle.setAttribute('cy', y + height);
                    }
                    
                    const syncIndicator = target.querySelector('.zone-sync-indicator');
                    if (syncIndicator) {
                        syncIndicator.setAttribute('cx', x + width - 10);
                        syncIndicator.setAttribute('cy', y + 10);
                    }
                    
                    // Update child racks
                    const racks = target.querySelectorAll('.draggable-rack');
                    racks.forEach(rack => {
                        const rackX = parseFloat(rack.getAttribute('data-x')) || 0;
                        const rackY = parseFloat(rack.getAttribute('data-y')) || 0;
                        const rackWidth = parseFloat(rack.getAttribute('data-width')) || 80;
                        const rackHeight = parseFloat(rack.getAttribute('data-height')) || 60;
                        const rackRect = rack.querySelector('.rack-rect');
                        if (rackRect) {
                            rackRect.setAttribute('x', x + rackX);
                            rackRect.setAttribute('y', y + rackY);
                        }
                        const rackText = rack.querySelector('text');
                        if (rackText) {
                            rackText.setAttribute('x', x + rackX + rackWidth / 2);
                            rackText.setAttribute('y', y + rackY + rackHeight / 2);
                        }
                        const rackSyncIndicator = rack.querySelector('.rack-sync-indicator');
                        if (rackSyncIndicator) {
                            rackSyncIndicator.setAttribute('cx', x + rackX + rackWidth - 8);
                            rackSyncIndicator.setAttribute('cy', y + rackY + 8);
                        }
                        const rackResizeHandle = rack.querySelector('.resize-handle-indicator');
                        if (rackResizeHandle) {
                            rackResizeHandle.setAttribute('cx', x + rackX + rackWidth);
                            rackResizeHandle.setAttribute('cy', y + rackY + rackHeight);
                        }
                        
                        // Update child shelves
                        const shelves = rack.querySelectorAll('.draggable-shelf');
                        shelves.forEach(shelf => {
                            const shelfX = parseFloat(shelf.getAttribute('data-x')) || 0;
                            const shelfY = parseFloat(shelf.getAttribute('data-y')) || 0;
                            const shelfRect = shelf.querySelector('.shelf-rect');
                            if (shelfRect) {
                                shelfRect.setAttribute('x', x + rackX + shelfX);
                                shelfRect.setAttribute('y', y + rackY + shelfY);
                            }
                            const shelfText = shelf.querySelector('text');
                            if (shelfText) {
                                shelfText.setAttribute('x', x + rackX + shelfX + 15);
                                shelfText.setAttribute('y', y + rackY + shelfY + 10);
                            }
                        });
                    });
                },
                onend: (event) => {
                    event.target.classList.remove('dragging');
                    const zoneId = event.target.getAttribute('data-zone-id');
                    const x = parseFloat(event.target.getAttribute('data-x')) || 0;
                    const y = parseFloat(event.target.getAttribute('data-y')) || 0;
                    
                    // Send update to server
                    this.updateZonePosition(zoneId, x, y);
                }
            });

        // Make zones resizable
        interact('.zone-rect')
            .resizable({
                edges: { left: false, right: true, bottom: true, top: false },
                listeners: {
                    move: (event) => {
                        const rect = event.target;
                        const zoneGroup = rect.closest('.draggable-zone');
                        if (!zoneGroup) return;
                        
                        const x = parseFloat(zoneGroup.getAttribute('data-x')) || 0;
                        const y = parseFloat(zoneGroup.getAttribute('data-y')) || 0;
                        let width = parseFloat(zoneGroup.getAttribute('data-width')) || 200;
                        let height = parseFloat(zoneGroup.getAttribute('data-height')) || 150;
                        
                        width += event.deltaRect.width;
                        height += event.deltaRect.height;
                        
                        // Minimum size
                        if (width < 50) width = 50;
                        if (height < 50) height = 50;
                        
                        zoneGroup.setAttribute('data-width', width);
                        zoneGroup.setAttribute('data-height', height);
                        
                        // Update rect size
                        rect.setAttribute('width', width);
                        rect.setAttribute('height', height);
                        
                        // Update text position (center)
                        const text = zoneGroup.querySelector('text');
                        if (text) {
                            text.setAttribute('x', x + width / 2);
                            text.setAttribute('y', y + height / 2);
                        }
                        
                        // Update resize handle indicator position
                        const resizeHandle = zoneGroup.querySelector('.resize-handle-indicator');
                        if (resizeHandle) {
                            resizeHandle.setAttribute('cx', x + width);
                            resizeHandle.setAttribute('cy', y + height);
                        }
                        
                        const syncIndicator = zoneGroup.querySelector('.zone-sync-indicator');
                        if (syncIndicator) {
                            syncIndicator.setAttribute('cx', x + width - 10);
                            syncIndicator.setAttribute('cy', y + 10);
                        }
                    }
                },
                modifiers: [
                    interact.modifiers.restrictSize({
                        min: { width: 50, height: 50 }
                    })
                ]
            })
            .on('resizeend', (event) => {
                const rect = event.target;
                const zoneGroup = rect.closest('.draggable-zone');
                if (!zoneGroup) return;
                
                const zoneId = zoneGroup.getAttribute('data-zone-id');
                const width = parseFloat(zoneGroup.getAttribute('data-width')) || 200;
                const height = parseFloat(zoneGroup.getAttribute('data-height')) || 150;
                
                // Send update to server
                this.updateZoneSize(zoneId, width, height);
            });

        // Make racks draggable
        interact('.draggable-rack')
            .draggable({
                onstart: (event) => {
                    event.target.classList.add('dragging');
                },
                onmove: (event) => {
                    const target = event.target;
                    const zone = target.closest('.draggable-zone');
                    const zoneX = parseFloat(zone.getAttribute('data-x')) || 0;
                    const zoneY = parseFloat(zone.getAttribute('data-y')) || 0;
                    const zoneWidth = parseFloat(zone.getAttribute('data-width')) || 0;
                    const zoneHeight = parseFloat(zone.getAttribute('data-height')) || 0;
                    
                    const rackWidth = parseFloat(target.getAttribute('data-width')) || 80;
                    const rackHeight = parseFloat(target.getAttribute('data-height')) || 60;
                    const maxX = Math.max(0, zoneWidth - rackWidth);
                    const maxY = Math.max(0, zoneHeight - rackHeight);
                    const newX = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const newY = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
                    const x = Math.min(Math.max(newX, 0), maxX);
                    const y = Math.min(Math.max(newY, 0), maxY);
                    
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);
                    
                    const rect = target.querySelector('.rack-rect');
                    const width = rackWidth;
                    const height = rackHeight;
                    
                    if (rect) {
                        rect.setAttribute('x', zoneX + x);
                        rect.setAttribute('y', zoneY + y);
                    }
                    
                    const text = target.querySelector('text');
                    if (text) {
                        text.setAttribute('x', zoneX + x + width / 2);
                        text.setAttribute('y', zoneY + y + height / 2);
                    }
                    
                    const rackSyncIndicator = target.querySelector('.rack-sync-indicator');
                    if (rackSyncIndicator) {
                        rackSyncIndicator.setAttribute('cx', zoneX + x + width - 8);
                        rackSyncIndicator.setAttribute('cy', zoneY + y + 8);
                    }
                    
                    // Update resize handle indicator
                    const resizeHandle = target.querySelector('.resize-handle-indicator');
                    if (resizeHandle) {
                        resizeHandle.setAttribute('cx', zoneX + x + width);
                        resizeHandle.setAttribute('cy', zoneY + y + height);
                    }
                    
                    // Update child shelves
                    const shelves = target.querySelectorAll('.draggable-shelf');
                    shelves.forEach(shelf => {
                        const shelfX = parseFloat(shelf.getAttribute('data-x')) || 0;
                        const shelfY = parseFloat(shelf.getAttribute('data-y')) || 0;
                        const shelfWidth = parseFloat(shelf.getAttribute('data-width')) || 60;
                        const shelfHeight = parseFloat(shelf.getAttribute('data-height')) || 20;
                        const shelfRect = shelf.querySelector('.shelf-rect');
                        if (shelfRect) {
                            shelfRect.setAttribute('x', zoneX + x + shelfX);
                            shelfRect.setAttribute('y', zoneY + y + shelfY);
                        }
                        const shelfText = shelf.querySelector('text');
                        if (shelfText) {
                            shelfText.setAttribute('x', zoneX + x + shelfX + shelfWidth / 2);
                            shelfText.setAttribute('y', zoneY + y + shelfY + shelfHeight / 2);
                        }
                        const shelfResizeHandle = shelf.querySelector('.resize-handle-indicator');
                        if (shelfResizeHandle) {
                            shelfResizeHandle.setAttribute('cx', zoneX + x + shelfX + shelfWidth);
                            shelfResizeHandle.setAttribute('cy', zoneY + y + shelfY + shelfHeight);
                        }
                    });
                },
                onend: (event) => {
                    event.target.classList.remove('dragging');
                    const rackId = event.target.getAttribute('data-rack-id');
                    const x = parseFloat(event.target.getAttribute('data-x')) || 0;
                    const y = parseFloat(event.target.getAttribute('data-y')) || 0;
                    
                    const serverMetrics = this.convertRackMetricsForServer(event.target, { x, y });
                    this.updateRackPosition(rackId, serverMetrics.x, serverMetrics.y);
                }
            });

        // Make racks resizable
        interact('.rack-rect')
            .resizable({
                edges: { left: false, right: true, bottom: true, top: false },
                listeners: {
                    move: (event) => {
                        const rect = event.target;
                        const rackGroup = rect.closest('.draggable-rack');
                        if (!rackGroup) return;
                        
                        const zone = rackGroup.closest('.draggable-zone');
                        const zoneX = parseFloat(zone.getAttribute('data-x')) || 0;
                        const zoneY = parseFloat(zone.getAttribute('data-y')) || 0;
                        const x = parseFloat(rackGroup.getAttribute('data-x')) || 0;
                        const y = parseFloat(rackGroup.getAttribute('data-y')) || 0;
                        let width = parseFloat(rackGroup.getAttribute('data-width')) || 80;
                        let height = parseFloat(rackGroup.getAttribute('data-height')) || 60;
                        
                        width += event.deltaRect.width;
                        height += event.deltaRect.height;
                        
                        if (width < 20) width = 20;
                        if (height < 20) height = 20;
                        
                        rackGroup.setAttribute('data-width', width);
                        rackGroup.setAttribute('data-height', height);
                        
                        rect.setAttribute('width', width);
                        rect.setAttribute('height', height);
                        
                        const text = rackGroup.querySelector('text');
                        if (text) {
                            text.setAttribute('x', zoneX + x + width / 2);
                            text.setAttribute('y', zoneY + y + height / 2);
                        }
                        
                        const rackSyncIndicator = rackGroup.querySelector('.rack-sync-indicator');
                        if (rackSyncIndicator) {
                            rackSyncIndicator.setAttribute('cx', zoneX + x + width - 8);
                            rackSyncIndicator.setAttribute('cy', zoneY + y + 8);
                        }
                        
                        const resizeHandle = rackGroup.querySelector('.resize-handle-indicator');
                        if (resizeHandle) {
                            resizeHandle.setAttribute('cx', zoneX + x + width);
                            resizeHandle.setAttribute('cy', zoneY + y + height);
                        }
                        
                        // Update child shelves positions
                        const shelves = rackGroup.querySelectorAll('.draggable-shelf');
                        shelves.forEach(shelf => {
                            const shelfX = parseFloat(shelf.getAttribute('data-x')) || 0;
                            const shelfY = parseFloat(shelf.getAttribute('data-y')) || 0;
                            const shelfWidth = parseFloat(shelf.getAttribute('data-width')) || 60;
                            const shelfHeight = parseFloat(shelf.getAttribute('data-height')) || 20;
                            const shelfRect = shelf.querySelector('.shelf-rect');
                            if (shelfRect) {
                                shelfRect.setAttribute('x', zoneX + x + shelfX);
                                shelfRect.setAttribute('y', zoneY + y + shelfY);
                            }
                            const shelfText = shelf.querySelector('text');
                            if (shelfText) {
                                shelfText.setAttribute('x', zoneX + x + shelfX + shelfWidth / 2);
                                shelfText.setAttribute('y', zoneY + y + shelfY + shelfHeight / 2);
                            }
                            const shelfResizeHandle = shelf.querySelector('.resize-handle-indicator');
                            if (shelfResizeHandle) {
                                shelfResizeHandle.setAttribute('cx', zoneX + x + shelfX + shelfWidth);
                                shelfResizeHandle.setAttribute('cy', zoneY + y + shelfY + shelfHeight);
                            }
                        });
                    }
                },
                modifiers: [
                    interact.modifiers.restrictSize({
                        min: { width: 20, height: 20 }
                    })
                ]
            })
            .on('resizeend', (event) => {
                const rect = event.target;
                const rackGroup = rect.closest('.draggable-rack');
                if (!rackGroup) return;
                
                const rackId = rackGroup.getAttribute('data-rack-id');
                const width = parseFloat(rackGroup.getAttribute('data-width')) || 80;
                const height = parseFloat(rackGroup.getAttribute('data-height')) || 60;
                
                const serverMetrics = this.convertRackMetricsForServer(rackGroup, { width, height });
                this.updateRackSize(rackId, serverMetrics.width, serverMetrics.height);
            });

        // Make shelves draggable
        interact('.draggable-shelf')
            .draggable({
                onstart: (event) => {
                    event.target.classList.add('dragging');
                },
                onmove: (event) => {
                    const target = event.target;
                    const rack = target.closest('.draggable-rack');
                    const zone = target.closest('.draggable-zone');
                    const zoneX = parseFloat(zone.getAttribute('data-x')) || 0;
                    const zoneY = parseFloat(zone.getAttribute('data-y')) || 0;
                    const rackX = parseFloat(rack.getAttribute('data-x')) || 0;
                    const rackY = parseFloat(rack.getAttribute('data-y')) || 0;
                    const rackWidth = parseFloat(rack.getAttribute('data-width')) || 0;
                    const rackHeight = parseFloat(rack.getAttribute('data-height')) || 0;
                    
                    const shelfWidth = parseFloat(target.getAttribute('data-width')) || 60;
                    const shelfHeight = parseFloat(target.getAttribute('data-height')) || 20;
                    const maxX = Math.max(0, rackWidth - shelfWidth);
                    const maxY = Math.max(0, rackHeight - shelfHeight);
                    const newX = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const newY = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
                    const x = Math.min(Math.max(newX, 0), maxX);
                    const y = Math.min(Math.max(newY, 0), maxY);
                    
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);
                    
                    const rect = target.querySelector('.shelf-rect');
                    const width = shelfWidth;
                    const height = shelfHeight;
                    
                    if (rect) {
                        rect.setAttribute('x', zoneX + rackX + x);
                        rect.setAttribute('y', zoneY + rackY + y);
                    }
                    
                    const text = target.querySelector('text');
                    if (text) {
                        text.setAttribute('x', zoneX + rackX + x + width / 2);
                        text.setAttribute('y', zoneY + rackY + y + height / 2);
                    }
                    
                    const resizeHandle = target.querySelector('.resize-handle-indicator');
                    if (resizeHandle) {
                        resizeHandle.setAttribute('cx', zoneX + rackX + x + width);
                        resizeHandle.setAttribute('cy', zoneY + rackY + y + height);
                    }
                },
                onend: (event) => {
                    event.target.classList.remove('dragging');
                    const shelfId = event.target.getAttribute('data-shelf-id');
                    const x = parseFloat(event.target.getAttribute('data-x')) || 0;
                    const y = parseFloat(event.target.getAttribute('data-y')) || 0;
                    
                    const serverMetrics = this.convertShelfMetricsForServer(event.target, { x, y });
                    this.updateShelfPosition(shelfId, serverMetrics.x, serverMetrics.y);
                }
            });

        // Make shelves resizable
        interact('.shelf-rect')
            .resizable({
                edges: { left: false, right: true, bottom: true, top: false },
                listeners: {
                    move: (event) => {
                        const rect = event.target;
                        const shelfGroup = rect.closest('.draggable-shelf');
                        if (!shelfGroup) return;
                        
                        const rack = shelfGroup.closest('.draggable-rack');
                        const zone = shelfGroup.closest('.draggable-zone');
                        const zoneX = parseFloat(zone.getAttribute('data-x')) || 0;
                        const zoneY = parseFloat(zone.getAttribute('data-y')) || 0;
                        const rackX = parseFloat(rack.getAttribute('data-x')) || 0;
                        const rackY = parseFloat(rack.getAttribute('data-y')) || 0;
                        const x = parseFloat(shelfGroup.getAttribute('data-x')) || 0;
                        const y = parseFloat(shelfGroup.getAttribute('data-y')) || 0;
                        let width = parseFloat(shelfGroup.getAttribute('data-width')) || 60;
                        let height = parseFloat(shelfGroup.getAttribute('data-height')) || 20;
                        
                        width += event.deltaRect.width;
                        height += event.deltaRect.height;
                        
                        if (width < 15) width = 15;
                        if (height < 10) height = 10;
                        
                        shelfGroup.setAttribute('data-width', width);
                        shelfGroup.setAttribute('data-height', height);
                        
                        rect.setAttribute('width', width);
                        rect.setAttribute('height', height);
                        
                        const text = shelfGroup.querySelector('text');
                        if (text) {
                            text.setAttribute('x', zoneX + rackX + x + width / 2);
                            text.setAttribute('y', zoneY + rackY + y + height / 2);
                        }
                        
                        const resizeHandle = shelfGroup.querySelector('.resize-handle-indicator');
                        if (resizeHandle) {
                            resizeHandle.setAttribute('cx', zoneX + rackX + x + width);
                            resizeHandle.setAttribute('cy', zoneY + rackY + y + height);
                        }
                    }
                },
                modifiers: [
                    interact.modifiers.restrictSize({
                        min: { width: 15, height: 10 }
                    })
                ]
            })
            .on('resizeend', (event) => {
                const rect = event.target;
                const shelfGroup = rect.closest('.draggable-shelf');
                if (!shelfGroup) return;
                
                const shelfId = shelfGroup.getAttribute('data-shelf-id');
                const width = parseFloat(shelfGroup.getAttribute('data-width')) || 60;
                const height = parseFloat(shelfGroup.getAttribute('data-height')) || 20;
                
                const serverMetrics = this.convertShelfMetricsForServer(shelfGroup, { width, height });
                this.updateShelfSize(shelfId, serverMetrics.width, serverMetrics.height);
            });
    }

    setupClickToEdit() {
        // Use direct event listeners on zone-rect elements
        if (!this.svg) {
            console.error('SVG element not found');
            return;
        }
        
        console.log('Setting up click to edit');
        
        // Helper function to select element
        const selectElement = (element, type) => {
            // Remove selection from all elements
            document.querySelectorAll('.draggable-zone.selected, .draggable-rack.selected, .draggable-shelf.selected').forEach(el => {
                el.classList.remove('selected');
            });
            // Select current element
            if (element) {
                element.classList.add('selected');
            }
        };
        
        // Helper function to get element group
        const getElementGroup = (target, className) => {
            if (target.classList && target.classList.contains(className)) {
                return target;
            }
            let parent = target.parentElement;
            while (parent && parent !== this.svg) {
                if (parent.classList && parent.classList.contains(className)) {
                    return parent;
                }
                parent = parent.parentElement;
            }
            return null;
        };
        
        // Wait a bit for elements to be rendered, then attach listeners
        setTimeout(() => {
            // Handle zones - single click selects, double click edits
            const zoneRects = document.querySelectorAll('.zone-rect');
            console.log('Found zone-rect elements:', zoneRects.length);
            
            zoneRects.forEach((rect) => {
                let clickTimer = null;
                let hasMoved = false;
                let mouseDownPos = { x: 0, y: 0 };
                
                rect.addEventListener('mousedown', (e) => {
                    mouseDownPos = { x: e.clientX, y: e.clientY };
                    hasMoved = false;
                });
                
                rect.addEventListener('mousemove', (e) => {
                    if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                        const distance = Math.sqrt(
                            Math.pow(e.clientX - mouseDownPos.x, 2) + 
                            Math.pow(e.clientY - mouseDownPos.y, 2)
                        );
                        if (distance > 5) {
                            hasMoved = true;
                        }
                    }
                });
                
                rect.addEventListener('click', (e) => {
                    if (hasMoved) {
                        hasMoved = false;
                        mouseDownPos = { x: 0, y: 0 };
                        return;
                    }
                    
                    const zoneGroup = getElementGroup(rect, 'draggable-zone');
                    if (!zoneGroup || zoneGroup.classList.contains('dragging')) {
                        return;
                    }
                    
                    // Single click - select
                    if (clickTimer === null) {
                        clickTimer = setTimeout(() => {
                            clickTimer = null;
                            selectElement(zoneGroup, 'zone');
                        }, 300); // Wait 300ms to see if it's a double click
                    } else {
                        // Double click - enter/exit zone focus
                        clearTimeout(clickTimer);
                        clickTimer = null;
                        e.stopPropagation();
                        const zoneId = zoneGroup.getAttribute('data-zone-id');
                        if (zoneId) {
                            if (this.zoneMode.activeZoneId === zoneId) {
                                this.navigateToZone(null);
                            } else {
                                this.navigateToZone(zoneId);
                            }
                        }
                    }
                    
                    mouseDownPos = { x: 0, y: 0 };
                });
            });

            // Handle racks - single click selects, double click enters rack view
            document.querySelectorAll('.draggable-rack, .rack-rect').forEach(element => {
                let clickTimer = null;
                let hasMoved = false;
                let mouseDownPos = { x: 0, y: 0 };
                
                element.addEventListener('mousedown', (e) => {
                    if (e.target.closest('.draggable-shelf')) return;
                    mouseDownPos = { x: e.clientX, y: e.clientY };
                    hasMoved = false;
                });
                
                element.addEventListener('mousemove', (e) => {
                    if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                        const distance = Math.sqrt(
                            Math.pow(e.clientX - mouseDownPos.x, 2) + 
                            Math.pow(e.clientY - mouseDownPos.y, 2)
                        );
                        if (distance > 5) {
                            hasMoved = true;
                        }
                    }
                });
                
                element.addEventListener('click', (e) => {
                    if (e.target.closest('.draggable-shelf')) return;
                    if (hasMoved) {
                        hasMoved = false;
                        mouseDownPos = { x: 0, y: 0 };
                        return;
                    }
                    
                    const rackGroup = getElementGroup(element, 'draggable-rack');
                    if (!rackGroup || rackGroup.classList.contains('dragging')) {
                        return;
                    }
                    
                    // Single click - select
                    if (clickTimer === null) {
                        clickTimer = setTimeout(() => {
                            clickTimer = null;
                            selectElement(rackGroup, 'rack');
                        }, 300);
                    } else {
                        // Double click - enter/exit rack focus
                        clearTimeout(clickTimer);
                        clickTimer = null;
                        e.stopPropagation();
                        const rackId = rackGroup.getAttribute('data-rack-id');
                        const zoneGroup = rackGroup.closest('.draggable-zone');
                        const zoneId = zoneGroup ? zoneGroup.getAttribute('data-zone-id') : this.zoneMode.activeZoneId;
                        if (rackId && zoneId) {
                            if (this.rackMode.activeRackId === rackId) {
                                this.navigateToRack(zoneId, null);
                            } else {
                                this.navigateToRack(zoneId, rackId);
                            }
                        }
                    }
                    
                    mouseDownPos = { x: 0, y: 0 };
                });
            });

            // Handle shelves - single click selects, double click edits
            document.querySelectorAll('.draggable-shelf, .shelf-rect').forEach(element => {
                let clickTimer = null;
                let hasMoved = false;
                let mouseDownPos = { x: 0, y: 0 };
                
                element.addEventListener('mousedown', (e) => {
                    mouseDownPos = { x: e.clientX, y: e.clientY };
                    hasMoved = false;
                });
                
                element.addEventListener('mousemove', (e) => {
                    if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                        const distance = Math.sqrt(
                            Math.pow(e.clientX - mouseDownPos.x, 2) + 
                            Math.pow(e.clientY - mouseDownPos.y, 2)
                        );
                        if (distance > 5) {
                            hasMoved = true;
                        }
                    }
                });
                
                element.addEventListener('click', (e) => {
                    if (hasMoved) {
                        hasMoved = false;
                        mouseDownPos = { x: 0, y: 0 };
                        return;
                    }
                    
                    const shelfGroup = getElementGroup(element, 'draggable-shelf');
                    if (!shelfGroup || shelfGroup.classList.contains('dragging')) {
                        return;
                    }
                    
                    // Single click - select
                    if (clickTimer === null) {
                        clickTimer = setTimeout(() => {
                            clickTimer = null;
                            selectElement(shelfGroup, 'shelf');
                        }, 300);
                    } else {
                        // Double click - edit
                        clearTimeout(clickTimer);
                        clickTimer = null;
                        e.stopPropagation();
                        const shelfId = shelfGroup.getAttribute('data-shelf-id');
                        if (shelfId) {
                            this.editShelf(shelfId);
                        }
                    }
                    
                    mouseDownPos = { x: 0, y: 0 };
                });
            });
        }, 500); // Wait 500ms for elements to render
    }

    setupContextMenu() {
        if (!this.svg) return;
        
        let contextMenu = null;
        const warehouseId = this.warehouseId;
        
        // Helper function to create context menu
        const createContextMenu = (x, y, items) => {
            // Remove existing menu
            if (contextMenu) {
                contextMenu.remove();
            }
            
            contextMenu = document.createElement('div');
            contextMenu.className = 'context-menu';
            contextMenu.style.position = 'fixed';
            contextMenu.style.left = x + 'px';
            contextMenu.style.top = y + 'px';
            contextMenu.style.zIndex = '10000';
            
            items.forEach((item, index) => {
                if (item === 'divider') {
                    const divider = document.createElement('div');
                    divider.className = 'context-menu-divider';
                    contextMenu.appendChild(divider);
                } else {
                    const menuItem = document.createElement('div');
                    menuItem.className = 'context-menu-item';
                    menuItem.innerHTML = `<i class="${item.icon}"></i>${item.label}`;
                    menuItem.addEventListener('click', (e) => {
                        e.stopPropagation();
                        item.action();
                        contextMenu.remove();
                        contextMenu = null;
                    });
                    contextMenu.appendChild(menuItem);
                }
            });
            
            document.body.appendChild(contextMenu);
        };
        
        // Close menu on click outside
        document.addEventListener('click', () => {
            if (contextMenu) {
                contextMenu.remove();
                contextMenu = null;
            }
        });
        
        const openZoneCreateModal = () => {
            if (!warehouseId) {
                console.error('Warehouse ID is missing, cannot create zone.');
                return;
            }
            if (typeof htmx !== 'undefined') {
                htmx.ajax('GET', `/wms-builder/warehouses/${warehouseId}/zones/create/`, {
                    target: '#modalBody',
                    swap: 'innerHTML'
                }).then(() => {
                    const modalElement = document.getElementById('dynamicModal');
                    if (modalElement) {
                        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                        modal.show();
                    }
                });
            }
        };
        
        // Context menu for zones, racks, and shelves
        this.svg.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            
            let target = e.target;
            
            // Check for zone - can be clicked on rect, text, or resize handle
            let zoneGroup = null;
            if (target.classList && target.classList.contains('zone-rect')) {
                zoneGroup = target.closest('.draggable-zone');
            } else if (target.tagName === 'text') {
                zoneGroup = target.closest('.draggable-zone');
            } else if (target.classList && target.classList.contains('resize-handle-indicator')) {
                zoneGroup = target.closest('.draggable-zone');
            }
            
            if (zoneGroup) {
                const zoneId = zoneGroup.getAttribute('data-zone-id');
                if (!zoneId) return;
                const isZoneFocused = this.zoneMode.activeZoneId === zoneId;
                
                createContextMenu(e.clientX, e.clientY, [
                    {
                        icon: 'fas fa-plus',
                        label: 'Dodaj regał',
                        action: () => {
                            if (typeof htmx !== 'undefined') {
                                htmx.ajax('GET', `/wms-builder/zones/${zoneId}/racks/create/`, {
                                    target: '#modalBody',
                                    swap: 'innerHTML'
                                }).then(() => {
                                    const modalElement = document.getElementById('dynamicModal');
                                    if (modalElement) {
                                        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                                        modal.show();
                                    }
                                });
                            }
                        }
                    },
                    'divider',
                    {
                        icon: 'fas fa-sync',
                        label: zoneGroup.querySelector('[data-synced="true"]') ? 'Edytuj synchronizację' : 'Synchronizuj z WMS',
                        action: () => {
                            this.syncZone(zoneId);
                        }
                    },
                    {
                        icon: isZoneFocused ? 'fas fa-door-open' : 'fas fa-door-open',
                        label: isZoneFocused ? 'Wyjdź ze strefy' : 'Wejdź do strefy',
                        action: () => {
                            this.navigateToZone(isZoneFocused ? null : zoneId);
                        }
                    },
                    {
                        icon: 'fas fa-edit',
                        label: 'Edytuj strefę',
                        action: () => {
                            this.editZone(zoneId);
                        }
                    },
                    {
                        icon: 'fas fa-trash',
                        label: 'Usuń strefę',
                        action: () => {
                            if (confirm('Czy na pewno chcesz usunąć tę strefę? Wszystkie regały i półki również zostaną usunięte.')) {
                                const formData = new FormData();
                                formData.append('csrfmiddlewaretoken', this.getCsrfToken());
                                fetch(`/wms-builder/zones/${zoneId}/delete/`, {
                                    method: 'POST',
                                    body: formData
                                }).then(() => {
                                    window.location.reload();
                                });
                            }
                        }
                    }
                ]);
                return;
            }
            
            // Check for rack - can be clicked on rect, text, or group
            let rackGroup = null;
            if (target.classList && target.classList.contains('rack-rect')) {
                rackGroup = target.closest('.draggable-rack');
            } else if (target.tagName === 'text' && target.closest('.draggable-rack')) {
                rackGroup = target.closest('.draggable-rack');
            } else if (target.classList && target.classList.contains('draggable-rack')) {
                rackGroup = target;
            }
            
            if (rackGroup) {
                const rackId = rackGroup.getAttribute('data-rack-id');
                if (!rackId) return;
                const zoneGroup = rackGroup.closest('.draggable-zone');
                const zoneId = zoneGroup ? zoneGroup.getAttribute('data-zone-id') : this.zoneMode.activeZoneId;
                const isRackFocused = this.rackMode.activeRackId === rackId;
                
                createContextMenu(e.clientX, e.clientY, [
                    {
                        icon: 'fas fa-plus',
                        label: 'Dodaj półkę',
                        action: () => {
                            if (typeof htmx !== 'undefined') {
                                htmx.ajax('GET', `/wms-builder/racks/${rackId}/shelves/create/`, {
                                    target: '#modalBody',
                                    swap: 'innerHTML'
                                }).then(() => {
                                    const modalElement = document.getElementById('dynamicModal');
                                    if (modalElement) {
                                        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                                        modal.show();
                                    }
                                });
                            }
                        }
                    },
                    'divider',
                    {
                        icon: 'fas fa-sync',
                        label: rackGroup.querySelector('[data-synced="true"]') ? 'Edytuj synchronizację' : 'Synchronizuj z WMS',
                        action: () => {
                            this.syncRack(rackId);
                        }
                    },
                    {
                        icon: 'fas fa-door-open',
                        label: isRackFocused ? 'Wyjdź z regału' : 'Wejdź do regału',
                        action: () => {
                            if (zoneId) {
                                this.navigateToRack(zoneId, isRackFocused ? null : rackId);
                            }
                        }
                    },
                    'divider',
                    {
                        icon: 'fas fa-edit',
                        label: 'Edytuj regał',
                        action: () => {
                            this.editRack(rackId);
                        }
                    },
                    {
                        icon: 'fas fa-trash',
                        label: 'Usuń regał',
                        action: () => {
                            if (confirm('Czy na pewno chcesz usunąć ten regał? Wszystkie półki również zostaną usunięte.')) {
                                const formData = new FormData();
                                formData.append('csrfmiddlewaretoken', this.getCsrfToken());
                                fetch(`/wms-builder/racks/${rackId}/delete/`, {
                                    method: 'POST',
                                    body: formData
                                }).then(() => {
                                    window.location.reload();
                                });
                            }
                        }
                    }
                ]);
                return;
            }
            
            // Check for shelf - can be clicked on rect, text, or group
            let shelfGroup = null;
            if (target.classList && target.classList.contains('shelf-rect')) {
                shelfGroup = target.closest('.draggable-shelf');
            } else if (target.tagName === 'text' && target.closest('.draggable-shelf')) {
                shelfGroup = target.closest('.draggable-shelf');
            } else if (target.classList && target.classList.contains('draggable-shelf')) {
                shelfGroup = target;
            }
            
            if (shelfGroup) {
                const shelfId = shelfGroup.getAttribute('data-shelf-id');
                if (!shelfId) return;
                
                createContextMenu(e.clientX, e.clientY, [
                    {
                        icon: 'fas fa-sync',
                        label: shelfGroup.querySelector('[data-synced="true"]') ? 'Edytuj synchronizację' : 'Synchronizuj z WMS',
                        action: () => {
                            this.syncShelf(shelfId);
                        }
                    },
                    {
                        icon: 'fas fa-edit',
                        label: 'Edytuj półkę',
                        action: () => {
                            this.editShelf(shelfId);
                        }
                    },
                    {
                        icon: 'fas fa-trash',
                        label: 'Usuń półkę',
                        action: () => {
                            if (confirm('Czy na pewno chcesz usunąć tę półkę?')) {
                                const formData = new FormData();
                                formData.append('csrfmiddlewaretoken', this.getCsrfToken());
                                fetch(`/wms-builder/shelves/${shelfId}/delete/`, {
                                    method: 'POST',
                                    body: formData
                                }).then(() => {
                                    window.location.reload();
                                });
                            }
                        }
                    }
                ]);
                return;
            }
            
            const activeRackId = this.rackMode && this.rackMode.activeRackId;
            if (activeRackId) {
                createContextMenu(e.clientX, e.clientY, [
                    {
                        icon: 'fas fa-plus',
                        label: 'Dodaj półkę',
                        action: () => {
                            if (typeof htmx !== 'undefined') {
                                htmx.ajax('GET', `/wms-builder/racks/${activeRackId}/shelves/create/`, {
                                    target: '#modalBody',
                                    swap: 'innerHTML'
                                }).then(() => {
                                    const modalElement = document.getElementById('dynamicModal');
                                    if (modalElement) {
                                        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                                        modal.show();
                                    }
                                });
                            }
                        }
                    }
                ]);
                return;
            }

            const zoneModeActive = Boolean(this.zoneMode.activeZoneId);
            if (zoneModeActive) {
                const focusedZone = this.getZoneGroupById(this.zoneMode.activeZoneId);
                const zoneId = focusedZone ? focusedZone.getAttribute('data-zone-id') : null;
                if (zoneId) {
                    createContextMenu(e.clientX, e.clientY, [
                        {
                            icon: 'fas fa-plus',
                            label: 'Dodaj regał',
                            action: () => {
                                if (typeof htmx !== 'undefined') {
                                    htmx.ajax('GET', `/wms-builder/zones/${zoneId}/racks/create/`, {
                                        target: '#modalBody',
                                        swap: 'innerHTML'
                                    }).then(() => {
                                        const modalElement = document.getElementById('dynamicModal');
                                        if (modalElement) {
                                            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                                            modal.show();
                                        }
                                    });
                                }
                            }
                        }
                    ]);
                    return;
                }
            }
            
            createContextMenu(e.clientX, e.clientY, [
                {
                    icon: 'fas fa-plus',
                    label: 'Dodaj strefę',
                    action: openZoneCreateModal
                }
            ]);
        });
    }

    setupZoomControls() {
        const zoomIn = document.getElementById('zoomIn');
        const zoomOut = document.getElementById('zoomOut');
        const resetZoom = document.getElementById('resetZoom');

        if (zoomIn) {
            zoomIn.addEventListener('click', () => {
                this.currentZoom = Math.min(this.currentZoom + 0.1, 3);
                this.applyZoom();
            });
        }

        if (zoomOut) {
            zoomOut.addEventListener('click', () => {
                this.currentZoom = Math.max(this.currentZoom - 0.1, 0.5);
                this.applyZoom();
            });
        }

        if (resetZoom) {
            resetZoom.addEventListener('click', () => {
                this.currentZoom = 1;
                this.applyZoom();
            });
        }

        this.zoneMode.updateZonesVisibility = () => {
            const activeZoneId = this.zoneMode.activeZoneId;
            const activeRackId = this.rackMode && this.rackMode.activeRackId;
            const showAll = !activeZoneId;
            const zones = document.querySelectorAll('.draggable-zone');
            zones.forEach(zone => {
                const zoneRect = zone.querySelector('.zone-rect');
                const zoneText = zone.querySelector('text');
                const zoneHandle = zone.querySelector('.resize-handle-indicator');
                const zoneSyncIndicator = zone.querySelector('.zone-sync-indicator');
                const zoneId = zone.getAttribute('data-zone-id');
                const isActive = activeZoneId && zoneId === activeZoneId;

                zone.classList.toggle('zone-mode-hidden', !showAll && !isActive);
                zone.classList.toggle('zone-mode-active', isActive);

                if (zoneRect) {
                    zoneRect.style.pointerEvents = showAll ? 'auto' : 'none';
                    if (showAll) {
                        zoneRect.style.opacity = 0.3;
                        zoneRect.style.strokeOpacity = 1;
                        zoneRect.style.fillOpacity = 0.3;
                    } else if (isActive) {
                        zoneRect.style.opacity = 0;
                        zoneRect.style.strokeOpacity = 0;
                        zoneRect.style.fillOpacity = 0;
                    } else {
                        zoneRect.style.opacity = 0.05;
                        zoneRect.style.strokeOpacity = 0.2;
                        zoneRect.style.fillOpacity = 0.05;
                    }
                }
                if (zoneText) {
                    if (showAll) {
                        zoneText.style.opacity = 1;
                    } else if (isActive && activeRackId) {
                        zoneText.style.opacity = 0;
                    } else {
                        zoneText.style.opacity = isActive ? 0 : 0.2;
                    }
                }
                if (zoneHandle) {
                    zoneHandle.style.display = showAll || (isActive && !activeRackId) ? 'block' : 'none';
                }
                if (zoneSyncIndicator) {
                    zoneSyncIndicator.style.display = showAll || (isActive && !activeRackId) ? 'block' : 'none';
                }

                const racks = zone.querySelectorAll('.draggable-rack');
                racks.forEach(rack => {
                    const rackRect = rack.querySelector('.rack-rect');
                    const rackText = rack.querySelector('text');
                    const rackHandle = rack.querySelector('.resize-handle-indicator');
                    const rackSyncIndicator = rack.querySelector('.rack-sync-indicator');
                    const rackId = rack.getAttribute('data-rack-id');
                    const isRackFocused = activeRackId && rackId === activeRackId;

                    const shouldHideRack = (!showAll && !isActive) || (isActive && activeRackId && !isRackFocused);
                    if (shouldHideRack) {
                        rack.classList.add('zone-mode-hidden');
                        rack.style.pointerEvents = 'none';
                        rack.style.opacity = 0;
                    } else {
                        rack.classList.remove('zone-mode-hidden');
                        rack.style.pointerEvents = 'auto';
                        rack.style.opacity = 1;
                    }

                    const allowInteractions = showAll || isActive;
                    if (rackRect) {
                        rackRect.style.pointerEvents = allowInteractions && (!activeRackId || isRackFocused) ? 'auto' : 'none';
                    }
                    if (rackText) {
                        rackText.style.opacity = allowInteractions ? (activeRackId && !isRackFocused ? 0 : 1) : 0.2;
                    }
                    if (rackHandle) {
                        rackHandle.style.display = allowInteractions && (!activeRackId || isRackFocused) ? 'block' : 'none';
                    }
                    if (rackSyncIndicator) {
                        rackSyncIndicator.style.display = allowInteractions && (!activeRackId || isRackFocused) ? 'block' : 'none';
                    }
                });
            });
        };
    }

    setupZoneMode() {
        const zoneModeSelect = document.getElementById('zoneMode');
        this.zoneModeSelect = zoneModeSelect || null;
        const initialZoneId = this.svg && this.svg.dataset ? (this.svg.dataset.activeZoneId || null) : null;
        const initialRackId = this.svg && this.svg.dataset ? (this.svg.dataset.activeRackId || null) : null;

        if (zoneModeSelect) {
            if (initialZoneId) {
                zoneModeSelect.value = initialZoneId;
            }
            zoneModeSelect.addEventListener('change', () => {
                const selectedValue = zoneModeSelect.value;
                this.navigateToZone(selectedValue || null);
            });
        }

        this.setZoneMode(initialZoneId, { syncSelect: false });
        if (initialRackId && initialZoneId) {
            this.setRackMode(initialRackId);
        } else {
            this.setRackMode(null, { updateVisibility: false });
        }
    }

    setZoneMode(zoneId, options = {}) {
        const { syncSelect = true } = options;
        const normalized = zoneId ? String(zoneId) : null;
        const previousZoneId = this.zoneMode.activeZoneId;
        if (!normalized && this.rackMode.activeRackId) {
            this.setRackMode(null, { updateVisibility: false });
        }
        if (previousZoneId && (!normalized || previousZoneId !== normalized)) {
            this.setRackMode(null, { updateVisibility: false });
            const previousZone = this.getZoneGroupById(previousZoneId);
            this.restoreZoneWorkspace(previousZone);
        }
        this.zoneMode.activeZoneId = normalized;
        if (this.zoneModeSelect && syncSelect) {
            this.zoneModeSelect.value = normalized || '';
        }
        if (normalized) {
            const zoneGroup = this.getZoneGroupById(normalized);
            if (!zoneGroup) {
                this.zoneMode.activeZoneId = null;
                if (this.zoneModeSelect && syncSelect) {
                    this.zoneModeSelect.value = '';
                }
                if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                    this.zoneMode.updateZonesVisibility();
                }
                return;
            }
            this.prepareZoneWorkspace(zoneGroup);
            if (!this.rackMode.activeRackId) {
                this.setRackMode(null, { updateVisibility: false });
            }
        }
        if (typeof this.zoneMode.updateZonesVisibility === 'function') {
            this.zoneMode.updateZonesVisibility();
        }
    }

    getZoneGroupById(zoneId) {
        if (!zoneId || !this.svg) {
            return null;
        }
        return this.svg.querySelector(`#zone-${zoneId}`);
    }

    getRackGroupById(rackId) {
        if (!rackId || !this.svg) {
            return null;
        }
        return this.svg.querySelector(`#rack-${rackId}`);
    }

    setRackMode(rackId, options = {}) {
        const { updateVisibility = true } = options;
        const normalized = rackId ? String(rackId) : null;
        const previousRackId = this.rackMode.activeRackId;
        if (previousRackId === normalized) {
            return;
        }
        if (normalized && !this.zoneMode.activeZoneId) {
            return;
        }
        if (previousRackId && previousRackId !== normalized) {
            const previousRack = this.getRackGroupById(previousRackId);
            this.restoreRackWorkspace(previousRack);
        }
        if (!normalized && previousRackId) {
            const previousRack = this.getRackGroupById(previousRackId);
            this.restoreRackWorkspace(previousRack);
        }
        this.rackMode.activeRackId = normalized;
        if (normalized) {
            const rackGroup = this.getRackGroupById(normalized);
            if (!rackGroup) {
                this.rackMode.activeRackId = null;
            } else {
                this.prepareRackWorkspace(rackGroup);
            }
        }
        if (updateVisibility && typeof this.zoneMode.updateZonesVisibility === 'function') {
            this.zoneMode.updateZonesVisibility();
        }
    }

    navigateToZone(zoneId) {
        const fallbackBaseCandidate = window.location.pathname.replace(/zones\/\d+\/?$/, '');
        const fallbackBase = fallbackBaseCandidate.endsWith('/') ? fallbackBaseCandidate : `${fallbackBaseCandidate}/`;
        const baseUrlCandidate = (this.zoneModeSelect && this.zoneModeSelect.dataset.detailBase) || this.detailBaseUrl || fallbackBase;
        if (!baseUrlCandidate) {
            return;
        }
        const normalizedBase = baseUrlCandidate.endsWith('/') ? baseUrlCandidate : `${baseUrlCandidate}/`;
        const targetUrl = zoneId ? `${normalizedBase}zones/${zoneId}/` : normalizedBase;
        window.location.href = targetUrl;
    }

    navigateToRack(zoneId, rackId) {
        const fallbackBaseCandidate = window.location.pathname.replace(/zones\/\d+\/racks\/\d+\/?$/, '').replace(/zones\/\d+\/?$/, '');
        const fallbackBase = fallbackBaseCandidate.endsWith('/') ? fallbackBaseCandidate : `${fallbackBaseCandidate}/`;
        const baseUrlCandidate = (this.zoneModeSelect && this.zoneModeSelect.dataset.detailBase) || this.detailBaseUrl || fallbackBase;
        if (!baseUrlCandidate || !zoneId) {
            return;
        }
        const normalizedBase = baseUrlCandidate.endsWith('/') ? baseUrlCandidate : `${baseUrlCandidate}/`;
        const zoneUrl = `${normalizedBase}zones/${zoneId}/`;
        const targetUrl = rackId ? `${zoneUrl}racks/${rackId}/` : zoneUrl;
        window.location.href = targetUrl;
    }

    prepareZoneWorkspace(zoneGroup) {
        if (!zoneGroup || zoneGroup.dataset.workspaceMode === '1') {
            return;
        }
        const zoneWidth = parseFloat(zoneGroup.getAttribute('data-width')) || 1;
        const zoneHeight = parseFloat(zoneGroup.getAttribute('data-height')) || 1;
        const zoneX = parseFloat(zoneGroup.getAttribute('data-x')) || 0;
        const zoneY = parseFloat(zoneGroup.getAttribute('data-y')) || 0;
        const workspaceWidth = this.zoneMode.workspaceWidth || zoneWidth;
        const workspaceHeight = this.zoneMode.workspaceHeight || zoneHeight;

        zoneGroup.dataset.zoneOriginalX = zoneX;
        zoneGroup.dataset.zoneOriginalY = zoneY;
        zoneGroup.dataset.zoneOriginalWidth = zoneWidth;
        zoneGroup.dataset.zoneOriginalHeight = zoneHeight;
        zoneGroup.dataset.workspaceWidth = workspaceWidth;
        zoneGroup.dataset.workspaceHeight = workspaceHeight;
        zoneGroup.dataset.workspaceMode = '1';

        zoneGroup.setAttribute('data-x', '0');
        zoneGroup.setAttribute('data-y', '0');
        zoneGroup.setAttribute('data-width', workspaceWidth);
        zoneGroup.setAttribute('data-height', workspaceHeight);

        const zoneRect = zoneGroup.querySelector('.zone-rect');
        if (zoneRect) {
            zoneRect.setAttribute('x', 0);
            zoneRect.setAttribute('y', 0);
            zoneRect.setAttribute('width', workspaceWidth);
            zoneRect.setAttribute('height', workspaceHeight);
        }

        const zoneHandle = zoneGroup.querySelector('.resize-handle-indicator');
        if (zoneHandle) {
            zoneHandle.setAttribute('cx', workspaceWidth);
            zoneHandle.setAttribute('cy', workspaceHeight);
        }

        const racks = zoneGroup.querySelectorAll('.draggable-rack');
        racks.forEach(rack => {
            this.convertRackToWorkspace(rack, zoneWidth, zoneHeight, workspaceWidth, workspaceHeight);
        });
    }

    restoreZoneWorkspace(zoneGroup) {
        if (!zoneGroup || zoneGroup.dataset.workspaceMode !== '1') {
            return;
        }
        const workspaceWidth = parseFloat(zoneGroup.getAttribute('data-width')) || 1;
        const workspaceHeight = parseFloat(zoneGroup.getAttribute('data-height')) || 1;
        const zoneWidth = parseFloat(zoneGroup.dataset.zoneOriginalWidth) || workspaceWidth;
        const zoneHeight = parseFloat(zoneGroup.dataset.zoneOriginalHeight) || workspaceHeight;
        const zoneX = parseFloat(zoneGroup.dataset.zoneOriginalX) || 0;
        const zoneY = parseFloat(zoneGroup.dataset.zoneOriginalY) || 0;

        const racks = zoneGroup.querySelectorAll('.draggable-rack');
        racks.forEach(rack => {
            this.convertRackFromWorkspace(rack, zoneWidth, zoneHeight, workspaceWidth, workspaceHeight, zoneX, zoneY);
        });

        zoneGroup.setAttribute('data-x', zoneX);
        zoneGroup.setAttribute('data-y', zoneY);
        zoneGroup.setAttribute('data-width', zoneWidth);
        zoneGroup.setAttribute('data-height', zoneHeight);
        delete zoneGroup.dataset.workspaceMode;
        delete zoneGroup.dataset.workspaceWidth;
        delete zoneGroup.dataset.workspaceHeight;
        delete zoneGroup.dataset.zoneOriginalX;
        delete zoneGroup.dataset.zoneOriginalY;
        delete zoneGroup.dataset.zoneOriginalWidth;
        delete zoneGroup.dataset.zoneOriginalHeight;

        const zoneRect = zoneGroup.querySelector('.zone-rect');
        if (zoneRect) {
            zoneRect.setAttribute('x', zoneX);
            zoneRect.setAttribute('y', zoneY);
            zoneRect.setAttribute('width', zoneWidth);
            zoneRect.setAttribute('height', zoneHeight);
        }

        const zoneHandle = zoneGroup.querySelector('.resize-handle-indicator');
        if (zoneHandle) {
            zoneHandle.setAttribute('cx', zoneX + zoneWidth);
            zoneHandle.setAttribute('cy', zoneY + zoneHeight);
        }
    }

    prepareRackWorkspace(rackGroup) {
        if (!rackGroup || rackGroup.dataset.rackWorkspaceMode === '1') {
            return;
        }
        const rackWidth = parseFloat(rackGroup.getAttribute('data-width')) || 1;
        const rackHeight = parseFloat(rackGroup.getAttribute('data-height')) || 1;
        const rackX = parseFloat(rackGroup.getAttribute('data-x')) || 0;
        const rackY = parseFloat(rackGroup.getAttribute('data-y')) || 0;
        const workspaceWidth = this.zoneMode.workspaceWidth || rackWidth;
        const workspaceHeight = this.zoneMode.workspaceHeight || rackHeight;

        rackGroup.dataset.rackDetailOriginalX = rackX;
        rackGroup.dataset.rackDetailOriginalY = rackY;
        rackGroup.dataset.rackDetailOriginalWidth = rackWidth;
        rackGroup.dataset.rackDetailOriginalHeight = rackHeight;
        rackGroup.dataset.rackDetailWorkspaceWidth = workspaceWidth;
        rackGroup.dataset.rackDetailWorkspaceHeight = workspaceHeight;
        rackGroup.dataset.rackWorkspaceMode = '1';

        rackGroup.setAttribute('data-x', '0');
        rackGroup.setAttribute('data-y', '0');
        rackGroup.setAttribute('data-width', workspaceWidth);
        rackGroup.setAttribute('data-height', workspaceHeight);

        const rackRect = rackGroup.querySelector('.rack-rect');
        if (rackRect) {
            rackRect.setAttribute('x', 0);
            rackRect.setAttribute('y', 0);
            rackRect.setAttribute('width', workspaceWidth);
            rackRect.setAttribute('height', workspaceHeight);
        }

        const rackHandle = rackGroup.querySelector('.resize-handle-indicator');
        if (rackHandle) {
            rackHandle.setAttribute('cx', workspaceWidth);
            rackHandle.setAttribute('cy', workspaceHeight);
        }

        const rackText = rackGroup.querySelector('text');
        if (rackText) {
            rackText.setAttribute('x', workspaceWidth / 2);
            rackText.setAttribute('y', workspaceHeight / 2);
        }

        const rackSync = rackGroup.querySelector('.rack-sync-indicator');
        if (rackSync) {
            rackSync.setAttribute('cx', workspaceWidth - 8);
            rackSync.setAttribute('cy', 8);
        }

        const shelves = rackGroup.querySelectorAll('.draggable-shelf');
        shelves.forEach(shelf => {
            this.convertShelfToWorkspace(
                shelf,
                rackWidth,
                rackHeight,
                workspaceWidth,
                workspaceHeight,
                0,
                0
            );
        });
    }

    restoreRackWorkspace(rackGroup) {
        if (!rackGroup || rackGroup.dataset.rackWorkspaceMode !== '1') {
            return;
        }
        const workspaceWidth = parseFloat(rackGroup.dataset.rackDetailWorkspaceWidth) || 1;
        const workspaceHeight = parseFloat(rackGroup.dataset.rackDetailWorkspaceHeight) || 1;
        const rackWidth = parseFloat(rackGroup.dataset.rackDetailOriginalWidth) || workspaceWidth;
        const rackHeight = parseFloat(rackGroup.dataset.rackDetailOriginalHeight) || workspaceHeight;
        const rackX = parseFloat(rackGroup.dataset.rackDetailOriginalX) || 0;
        const rackY = parseFloat(rackGroup.dataset.rackDetailOriginalY) || 0;

        const shelves = rackGroup.querySelectorAll('.draggable-shelf');
        shelves.forEach(shelf => {
            this.convertShelfFromWorkspace(
                shelf,
                rackWidth,
                rackHeight,
                workspaceWidth,
                workspaceHeight,
                rackX,
                rackY
            );
        });

        rackGroup.setAttribute('data-x', rackX);
        rackGroup.setAttribute('data-y', rackY);
        rackGroup.setAttribute('data-width', rackWidth);
        rackGroup.setAttribute('data-height', rackHeight);

        delete rackGroup.dataset.rackWorkspaceMode;
        delete rackGroup.dataset.rackDetailOriginalX;
        delete rackGroup.dataset.rackDetailOriginalY;
        delete rackGroup.dataset.rackDetailOriginalWidth;
        delete rackGroup.dataset.rackDetailOriginalHeight;
        delete rackGroup.dataset.rackDetailWorkspaceWidth;
        delete rackGroup.dataset.rackDetailWorkspaceHeight;

        const rackRect = rackGroup.querySelector('.rack-rect');
        if (rackRect) {
            rackRect.setAttribute('x', rackX);
            rackRect.setAttribute('y', rackY);
            rackRect.setAttribute('width', rackWidth);
            rackRect.setAttribute('height', rackHeight);
        }

        const rackHandle = rackGroup.querySelector('.resize-handle-indicator');
        if (rackHandle) {
            rackHandle.setAttribute('cx', rackX + rackWidth);
            rackHandle.setAttribute('cy', rackY + rackHeight);
        }

        const rackText = rackGroup.querySelector('text');
        if (rackText) {
            rackText.setAttribute('x', rackX + rackWidth / 2);
            rackText.setAttribute('y', rackY + rackHeight / 2);
        }

        const rackSync = rackGroup.querySelector('.rack-sync-indicator');
        if (rackSync) {
            rackSync.setAttribute('cx', rackX + rackWidth - 8);
            rackSync.setAttribute('cy', rackY + 8);
        }
    }

    convertRackToWorkspace(rack, zoneWidth, zoneHeight, workspaceWidth, workspaceHeight) {
        if (!rack) {
            return;
        }
        const zone = rack.closest('.draggable-zone');
        const originalX = parseFloat(rack.getAttribute('data-x')) || 0;
        const originalY = parseFloat(rack.getAttribute('data-y')) || 0;
        const originalWidth = parseFloat(rack.getAttribute('data-width')) || 0;
        const originalHeight = parseFloat(rack.getAttribute('data-height')) || 0;

        const workspaceX = zoneWidth ? (originalX / zoneWidth) * workspaceWidth : originalX;
        const workspaceY = zoneHeight ? (originalY / zoneHeight) * workspaceHeight : originalY;
        const workspaceRackWidth = zoneWidth ? (originalWidth / zoneWidth) * workspaceWidth : originalWidth;
        const workspaceRackHeight = zoneHeight ? (originalHeight / zoneHeight) * workspaceHeight : originalHeight;

        rack.setAttribute('data-x', workspaceX);
        rack.setAttribute('data-y', workspaceY);
        rack.setAttribute('data-width', workspaceRackWidth);
        rack.setAttribute('data-height', workspaceRackHeight);

        const rect = rack.querySelector('.rack-rect');
        if (rect) {
            rect.setAttribute('x', workspaceX);
            rect.setAttribute('y', workspaceY);
            rect.setAttribute('width', workspaceRackWidth);
            rect.setAttribute('height', workspaceRackHeight);
        }

        const text = rack.querySelector('text');
        if (text) {
            text.setAttribute('x', workspaceX + workspaceRackWidth / 2);
            text.setAttribute('y', workspaceY + workspaceRackHeight / 2);
        }

        const rackHandle = rack.querySelector('.resize-handle-indicator');
        if (rackHandle) {
            rackHandle.setAttribute('cx', workspaceX + workspaceRackWidth);
            rackHandle.setAttribute('cy', workspaceY + workspaceRackHeight);
        }

        const racksync = rack.querySelector('.rack-sync-indicator');
        if (racksync) {
            racksync.setAttribute('cx', workspaceX + workspaceRackWidth - 8);
            racksync.setAttribute('cy', workspaceY + 8);
        }

        const shelves = rack.querySelectorAll('.draggable-shelf');
        shelves.forEach(shelf => {
            this.convertShelfToWorkspace(shelf, originalWidth, originalHeight, workspaceRackWidth, workspaceRackHeight, workspaceX, workspaceY);
        });
    }

    convertRackFromWorkspace(rack, zoneWidth, zoneHeight, workspaceWidth, workspaceHeight, zoneX, zoneY) {
        if (!rack) {
            return;
        }
        const workspaceX = parseFloat(rack.getAttribute('data-x')) || 0;
        const workspaceY = parseFloat(rack.getAttribute('data-y')) || 0;
        const workspaceRackWidth = parseFloat(rack.getAttribute('data-width')) || 0;
        const workspaceRackHeight = parseFloat(rack.getAttribute('data-height')) || 0;

        const zoneXValue = workspaceWidth ? (workspaceX / workspaceWidth) * zoneWidth : workspaceX;
        const zoneYValue = workspaceHeight ? (workspaceY / workspaceHeight) * zoneHeight : workspaceY;
        const zoneRackWidth = workspaceWidth ? (workspaceRackWidth / workspaceWidth) * zoneWidth : workspaceRackWidth;
        const zoneRackHeight = workspaceHeight ? (workspaceRackHeight / workspaceHeight) * zoneHeight : workspaceRackHeight;

        rack.setAttribute('data-x', zoneXValue);
        rack.setAttribute('data-y', zoneYValue);
        rack.setAttribute('data-width', zoneRackWidth);
        rack.setAttribute('data-height', zoneRackHeight);

        const rect = rack.querySelector('.rack-rect');
        if (rect) {
            rect.setAttribute('x', zoneX + zoneXValue);
            rect.setAttribute('y', zoneY + zoneYValue);
            rect.setAttribute('width', zoneRackWidth);
            rect.setAttribute('height', zoneRackHeight);
        }

        const text = rack.querySelector('text');
        if (text) {
            text.setAttribute('x', zoneX + zoneXValue + zoneRackWidth / 2);
            text.setAttribute('y', zoneY + zoneYValue + zoneRackHeight / 2);
        }

        const rackHandle = rack.querySelector('.resize-handle-indicator');
        if (rackHandle) {
            rackHandle.setAttribute('cx', zoneX + zoneXValue + zoneRackWidth);
            rackHandle.setAttribute('cy', zoneY + zoneYValue + zoneRackHeight);
        }

        const rackSync = rack.querySelector('.rack-sync-indicator');
        if (rackSync) {
            rackSync.setAttribute('cx', zoneX + zoneXValue + zoneRackWidth - 8);
            rackSync.setAttribute('cy', zoneY + zoneYValue + 8);
        }

        const shelves = rack.querySelectorAll('.draggable-shelf');
        shelves.forEach(shelf => {
            this.convertShelfFromWorkspace(shelf, zoneRackWidth, zoneRackHeight, workspaceRackWidth, workspaceRackHeight, zoneX + zoneXValue, zoneY + zoneYValue);
        });
    }

    convertShelfToWorkspace(shelf, rackWidth, rackHeight, workspaceRackWidth, workspaceRackHeight, rackX, rackY) {
        if (!shelf) {
            return;
        }
        const shelfX = parseFloat(shelf.getAttribute('data-x')) || 0;
        const shelfY = parseFloat(shelf.getAttribute('data-y')) || 0;
        const shelfWidth = parseFloat(shelf.getAttribute('data-width')) || 0;
        const shelfHeight = parseFloat(shelf.getAttribute('data-height')) || 0;

        const workspaceShelfX = rackWidth ? (shelfX / rackWidth) * workspaceRackWidth : shelfX;
        const workspaceShelfY = rackHeight ? (shelfY / rackHeight) * workspaceRackHeight : shelfY;
        const workspaceShelfWidth = rackWidth ? (shelfWidth / rackWidth) * workspaceRackWidth : shelfWidth;
        const workspaceShelfHeight = rackHeight ? (shelfHeight / rackHeight) * workspaceRackHeight : shelfHeight;

        shelf.setAttribute('data-x', workspaceShelfX);
        shelf.setAttribute('data-y', workspaceShelfY);
        shelf.setAttribute('data-width', workspaceShelfWidth);
        shelf.setAttribute('data-height', workspaceShelfHeight);

        const rect = shelf.querySelector('.shelf-rect');
        if (rect) {
            rect.setAttribute('x', rackX + workspaceShelfX);
            rect.setAttribute('y', rackY + workspaceShelfY);
            rect.setAttribute('width', workspaceShelfWidth);
            rect.setAttribute('height', workspaceShelfHeight);
        }

        const text = shelf.querySelector('text');
        if (text) {
            text.setAttribute('x', rackX + workspaceShelfX + workspaceShelfWidth / 2);
            text.setAttribute('y', rackY + workspaceShelfY + workspaceShelfHeight / 2);
        }

        const shelfHandle = shelf.querySelector('.resize-handle-indicator');
        if (shelfHandle) {
            shelfHandle.setAttribute('cx', rackX + workspaceShelfX + workspaceShelfWidth);
            shelfHandle.setAttribute('cy', rackY + workspaceShelfY + workspaceShelfHeight);
        }
    }

    convertShelfFromWorkspace(shelf, zoneRackWidth, zoneRackHeight, workspaceRackWidth, workspaceRackHeight, rackX, rackY) {
        if (!shelf) {
            return;
        }
        const workspaceShelfX = parseFloat(shelf.getAttribute('data-x')) || 0;
        const workspaceShelfY = parseFloat(shelf.getAttribute('data-y')) || 0;
        const workspaceShelfWidth = parseFloat(shelf.getAttribute('data-width')) || 0;
        const workspaceShelfHeight = parseFloat(shelf.getAttribute('data-height')) || 0;

        const zoneShelfX = workspaceRackWidth ? (workspaceShelfX / workspaceRackWidth) * zoneRackWidth : workspaceShelfX;
        const zoneShelfY = workspaceRackHeight ? (workspaceShelfY / workspaceRackHeight) * zoneRackHeight : workspaceShelfY;
        const zoneShelfWidth = workspaceRackWidth ? (workspaceShelfWidth / workspaceRackWidth) * zoneRackWidth : workspaceShelfWidth;
        const zoneShelfHeight = workspaceRackHeight ? (workspaceShelfHeight / workspaceRackHeight) * zoneRackHeight : workspaceShelfHeight;

        shelf.setAttribute('data-x', zoneShelfX);
        shelf.setAttribute('data-y', zoneShelfY);
        shelf.setAttribute('data-width', zoneShelfWidth);
        shelf.setAttribute('data-height', zoneShelfHeight);

        const rect = shelf.querySelector('.shelf-rect');
        if (rect) {
            rect.setAttribute('x', rackX + zoneShelfX);
            rect.setAttribute('y', rackY + zoneShelfY);
            rect.setAttribute('width', zoneShelfWidth);
            rect.setAttribute('height', zoneShelfHeight);
        }

        const text = shelf.querySelector('text');
        if (text) {
            text.setAttribute('x', rackX + zoneShelfX + zoneShelfWidth / 2);
            text.setAttribute('y', rackY + zoneShelfY + zoneShelfHeight / 2);
        }

        const shelfHandle = shelf.querySelector('.resize-handle-indicator');
        if (shelfHandle) {
            shelfHandle.setAttribute('cx', rackX + zoneShelfX + zoneShelfWidth);
            shelfHandle.setAttribute('cy', rackY + zoneShelfY + zoneShelfHeight);
        }
    }

    getZoneScaling(zone) {
        if (!zone || zone.dataset.workspaceMode !== '1') {
            return null;
        }
        return {
            workspaceWidth: parseFloat(zone.getAttribute('data-width')) || 1,
            workspaceHeight: parseFloat(zone.getAttribute('data-height')) || 1,
            zoneWidth: parseFloat(zone.dataset.zoneOriginalWidth) || 1,
            zoneHeight: parseFloat(zone.dataset.zoneOriginalHeight) || 1
        };
    }

    convertRackMetricsForServer(rack, metrics) {
        const zone = rack.closest('.draggable-zone');
        const scaling = this.getZoneScaling(zone);
        if (!scaling) {
            return metrics;
        }
        const converted = { ...metrics };
        if (typeof metrics.x === 'number') {
            converted.x = scaling.workspaceWidth ? (metrics.x / scaling.workspaceWidth) * scaling.zoneWidth : metrics.x;
        }
        if (typeof metrics.y === 'number') {
            converted.y = scaling.workspaceHeight ? (metrics.y / scaling.workspaceHeight) * scaling.zoneHeight : metrics.y;
        }
        if (typeof metrics.width === 'number') {
            converted.width = scaling.workspaceWidth ? (metrics.width / scaling.workspaceWidth) * scaling.zoneWidth : metrics.width;
        }
        if (typeof metrics.height === 'number') {
            converted.height = scaling.workspaceHeight ? (metrics.height / scaling.workspaceHeight) * scaling.zoneHeight : metrics.height;
        }
        return converted;
    }

    convertShelfMetricsForServer(shelf, metrics) {
        const rack = shelf.closest('.draggable-rack');
        if (!rack) {
            return metrics;
        }
        const rackWidth = parseFloat(rack.getAttribute('data-width')) || 1;
        const rackHeight = parseFloat(rack.getAttribute('data-height')) || 1;

        const detailZoneWidth = parseFloat(rack.dataset.rackDetailOriginalWidth || '') || null;
        const detailZoneHeight = parseFloat(rack.dataset.rackDetailOriginalHeight || '') || null;
        const detailWorkspaceWidth = parseFloat(rack.dataset.rackDetailWorkspaceWidth || '') || null;
        const detailWorkspaceHeight = parseFloat(rack.dataset.rackDetailWorkspaceHeight || '') || null;

        const rackSizeInZone = detailZoneWidth && detailZoneHeight
            ? { width: detailZoneWidth, height: detailZoneHeight }
            : this.convertRackMetricsForServer(rack, { width: rackWidth, height: rackHeight });

        const workspaceWidth = detailWorkspaceWidth || rackWidth;
        const workspaceHeight = detailWorkspaceHeight || rackHeight;
        const zoneRackWidth = rackSizeInZone.width || detailZoneWidth || rackWidth;
        const zoneRackHeight = rackSizeInZone.height || detailZoneHeight || rackHeight;

        const converted = { ...metrics };
        if (typeof metrics.x === 'number') {
            converted.x = workspaceWidth ? (metrics.x / workspaceWidth) * zoneRackWidth : metrics.x;
        }
        if (typeof metrics.y === 'number') {
            converted.y = workspaceHeight ? (metrics.y / workspaceHeight) * zoneRackHeight : metrics.y;
        }
        if (typeof metrics.width === 'number') {
            converted.width = workspaceWidth ? (metrics.width / workspaceWidth) * zoneRackWidth : metrics.width;
        }
        if (typeof metrics.height === 'number') {
            converted.height = workspaceHeight ? (metrics.height / workspaceHeight) * zoneRackHeight : metrics.height;
        }
        return converted;
    }

    applyZoom() {
        if (this.svg) {
            const width = parseFloat(this.svg.getAttribute('viewBox').split(' ')[2]);
            const height = parseFloat(this.svg.getAttribute('viewBox').split(' ')[3]);
            this.svg.style.width = (width * this.currentZoom) + 'px';
        }
    }

    updateZonePosition(zoneId, x, y) {
        const formData = new FormData();
        formData.append('x', x);
        formData.append('y', y);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/zones/${zoneId}/update-position/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update zone position');
            }
        });
    }

    updateZoneSize(zoneId, width, height) {
        const formData = new FormData();
        formData.append('width', width);
        formData.append('height', height);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/zones/${zoneId}/update-size/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update zone size');
            }
        });
    }

    updateRackPosition(rackId, x, y) {
        const formData = new FormData();
        formData.append('x', x);
        formData.append('y', y);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/racks/${rackId}/update-position/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update rack position');
            }
        });
    }

    updateRackSize(rackId, width, height) {
        const formData = new FormData();
        formData.append('width', width);
        formData.append('height', height);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/racks/${rackId}/update-size/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update rack size');
            }
        });
    }

    updateShelfPosition(shelfId, x, y) {
        const formData = new FormData();
        formData.append('x', x);
        formData.append('y', y);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/shelves/${shelfId}/update-position/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update shelf position');
            }
        });
    }

    updateShelfSize(shelfId, width, height) {
        const formData = new FormData();
        formData.append('width', width);
        formData.append('height', height);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/shelves/${shelfId}/update-size/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to update shelf size');
            }
        });
    }

    editZone(zoneId) {
        console.log('editZone called with zoneId:', zoneId);
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/zones/${zoneId}/edit/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                console.log('Modal content loaded');
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                    console.log('Modal shown');
                } else {
                    console.error('Modal element not found');
                }
            }).catch(error => {
                console.error('Error loading zone edit form:', error);
            });
        } else {
            console.error('HTMX not available');
        }
    }

    editRack(rackId) {
        console.log('editRack called with rackId:', rackId);
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/racks/${rackId}/edit/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                }
            }).catch(error => {
                console.error('Error loading rack edit form:', error);
            });
        }
    }

    editShelf(shelfId) {
        console.log('editShelf called with shelfId:', shelfId);
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/shelves/${shelfId}/edit/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                }
            }).catch(error => {
                console.error('Error loading shelf edit form:', error);
            });
        }
    }

    syncZone(zoneId) {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/zones/${zoneId}/sync-to-location/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                }
            }).catch(error => {
                console.error('Error loading zone sync form:', error);
            });
        }
    }

    syncRack(rackId) {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/racks/${rackId}/sync-to-location/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                }
            }).catch(error => {
                console.error('Error loading rack sync form:', error);
            });
        }
    }

    syncShelf(shelfId) {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/wms-builder/shelves/${shelfId}/sync-to-location/`, {
                target: '#modalBody',
                swap: 'innerHTML'
            }).then(() => {
                const modalElement = document.getElementById('dynamicModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                }
            }).catch(error => {
                console.error('Error loading shelf sync form:', error);
            });
        }
    }

    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

