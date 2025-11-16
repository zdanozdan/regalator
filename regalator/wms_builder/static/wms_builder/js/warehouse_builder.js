/**
 * Warehouse Builder - Drag and Drop functionality
 */

class WarehouseBuilder {
    constructor(warehouseData = {}) {
        this.warehouseData = warehouseData || {};
        this.svg = null;
        this.svgContainer = null;
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
        this.defaultBackground = '#f8f9fa';
        this.sizingLimits = {
            zone: { minWidth: 1, minHeight: 1 },
            rack: { minWidth: 1, minHeight: 1 },
            shelf: { minWidth: 1, minHeight: 1 }
        };
        this.defaultSizes = {
            zone: { width: 200, height: 150 },
            rack: { width: 80, height: 60 },
            shelf: { width: 30, height: 10 }
        };
        this.defaultColors = {
            zone: '#007bff',
            rack: '#28a745',
            shelf: '#ffc107'
        };
        this.currentSelection = { type: null, element: null };
        this.clipboard = null;
        this.clipboardShortcutsBound = false;
        this.clipboardOffset = 10;
        this.boundClipboardHandler = this.handleClipboardKeydown.bind(this);
        this.pointerPosition = null;
        this.pointerTrackingBound = false;
    }

    init() {
        console.log('WarehouseBuilder.init() called');
        this.svg = document.getElementById('warehouse-svg');
        this.svgContainer = document.getElementById('svg-container');
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
        this.setupClipboardShortcuts();
        this.setupPointerTracking();
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

                        const workspaceWidth = this.zoneMode.workspaceWidth || null;
                        const workspaceHeight = this.zoneMode.workspaceHeight || null;
                        const maxWidth = workspaceWidth && workspaceWidth > x ? workspaceWidth - x : Number.POSITIVE_INFINITY;
                        const maxHeight = workspaceHeight && workspaceHeight > y ? workspaceHeight - y : Number.POSITIVE_INFINITY;
                        const { minWidth, minHeight } = this.sizingLimits.zone;
                        
                        width = Math.min(Math.max(width, minWidth), maxWidth);
                        height = Math.min(Math.max(height, minHeight), maxHeight);
                        
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
                        min: {
                            width: this.sizingLimits.zone.minWidth,
                            height: this.sizingLimits.zone.minHeight
                        }
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

                        const zoneWidth = parseFloat(zone.getAttribute('data-width')) || 0;
                        const zoneHeight = parseFloat(zone.getAttribute('data-height')) || 0;
                        const maxWidth = zoneWidth > 0 ? Math.max(this.sizingLimits.rack.minWidth, zoneWidth - x) : Number.POSITIVE_INFINITY;
                        const maxHeight = zoneHeight > 0 ? Math.max(this.sizingLimits.rack.minHeight, zoneHeight - y) : Number.POSITIVE_INFINITY;
                        const { minWidth, minHeight } = this.sizingLimits.rack;
                        
                        width = Math.min(Math.max(width, minWidth), maxWidth);
                        height = Math.min(Math.max(height, minHeight), maxHeight);
                        
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
                        min: {
                            width: this.sizingLimits.rack.minWidth,
                            height: this.sizingLimits.rack.minHeight
                        }
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

                        const rackWidth = parseFloat(rack.getAttribute('data-width')) || 0;
                        const rackHeight = parseFloat(rack.getAttribute('data-height')) || 0;
                        const maxWidth = rackWidth > 0 ? Math.max(this.sizingLimits.shelf.minWidth, rackWidth - x) : Number.POSITIVE_INFINITY;
                        const maxHeight = rackHeight > 0 ? Math.max(this.sizingLimits.shelf.minHeight, rackHeight - y) : Number.POSITIVE_INFINITY;
                        const { minWidth, minHeight } = this.sizingLimits.shelf;
                        
                        width = Math.min(Math.max(width, minWidth), maxWidth);
                        height = Math.min(Math.max(height, minHeight), maxHeight);
                        
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
                        min: {
                            width: this.sizingLimits.shelf.minWidth,
                            height: this.sizingLimits.shelf.minHeight
                        }
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
        if (!this.svg) {
            console.error('SVG element not found');
            return;
        }

        const bindHandlers = () => {
            document.querySelectorAll('.zone-rect').forEach(rect => this.bindZoneSelectionHandlers(rect));
            document.querySelectorAll('.draggable-rack').forEach(rack => this.bindRackSelectionHandlers(rack));
            document.querySelectorAll('.draggable-shelf').forEach(shelf => this.bindShelfSelectionHandlers(shelf));
        };

        setTimeout(bindHandlers, 500);
    }

    bindZoneSelectionHandlers(rect) {
        if (!rect || rect.dataset.selectionBound === '1') {
            return;
        }
        rect.dataset.selectionBound = '1';
        let clickTimer = null;
        let hasMoved = false;
        let mouseDownPos = { x: 0, y: 0 };

        rect.addEventListener('mousedown', (e) => {
            mouseDownPos = { x: e.clientX, y: e.clientY };
            hasMoved = false;
        });

        rect.addEventListener('mousemove', (e) => {
            if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                const distance = Math.hypot(e.clientX - mouseDownPos.x, e.clientY - mouseDownPos.y);
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

            const zoneGroup = rect.closest('.draggable-zone');
            if (!zoneGroup || zoneGroup.classList.contains('dragging')) {
                return;
            }

            if (clickTimer === null) {
                clickTimer = setTimeout(() => {
                    clickTimer = null;
                    this.setSelection(zoneGroup, 'zone');
                }, 300);
            } else {
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
    }

    bindRackSelectionHandlers(rackGroup) {
        if (!rackGroup || rackGroup.dataset.selectionBound === '1') {
            return;
        }
        rackGroup.dataset.selectionBound = '1';
        let clickTimer = null;
        let hasMoved = false;
        let mouseDownPos = { x: 0, y: 0 };

        rackGroup.addEventListener('mousedown', (e) => {
            if (e.target.closest('.draggable-shelf')) return;
            mouseDownPos = { x: e.clientX, y: e.clientY };
            hasMoved = false;
        });

        rackGroup.addEventListener('mousemove', (e) => {
            if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                const distance = Math.hypot(e.clientX - mouseDownPos.x, e.clientY - mouseDownPos.y);
                if (distance > 5) {
                    hasMoved = true;
                }
            }
        });

        rackGroup.addEventListener('click', (e) => {
            if (e.target.closest('.draggable-shelf')) return;
            if (hasMoved) {
                hasMoved = false;
                mouseDownPos = { x: 0, y: 0 };
                return;
            }

            if (rackGroup.classList.contains('dragging')) {
                return;
            }

            if (clickTimer === null) {
                clickTimer = setTimeout(() => {
                    clickTimer = null;
                    this.setSelection(rackGroup, 'rack');
                }, 300);
            } else {
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
    }

    bindShelfSelectionHandlers(shelfGroup) {
        if (!shelfGroup || shelfGroup.dataset.selectionBound === '1') {
            return;
        }
        shelfGroup.dataset.selectionBound = '1';
        let clickTimer = null;
        let hasMoved = false;
        let mouseDownPos = { x: 0, y: 0 };

        shelfGroup.addEventListener('mousedown', (e) => {
            mouseDownPos = { x: e.clientX, y: e.clientY };
            hasMoved = false;
        });

        shelfGroup.addEventListener('mousemove', (e) => {
            if (mouseDownPos.x !== 0 || mouseDownPos.y !== 0) {
                const distance = Math.hypot(e.clientX - mouseDownPos.x, e.clientY - mouseDownPos.y);
                if (distance > 5) {
                    hasMoved = true;
                }
            }
        });

        shelfGroup.addEventListener('click', (e) => {
            if (hasMoved) {
                hasMoved = false;
                mouseDownPos = { x: 0, y: 0 };
                return;
            }

            if (shelfGroup.classList.contains('dragging')) {
                return;
            }

            if (clickTimer === null) {
                clickTimer = setTimeout(() => {
                    clickTimer = null;
                    this.setSelection(shelfGroup, 'shelf');
                }, 300);
            } else {
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
    }

    setSelection(element, type) {
        if (this.currentSelection && this.currentSelection.element === element) {
            return;
        }

        document.querySelectorAll('.draggable-zone.selected, .draggable-rack.selected, .draggable-shelf.selected').forEach(el => {
            if (el !== element) {
                el.classList.remove('selected');
            }
        });

        if (element) {
            element.classList.add('selected');
            this.currentSelection = { element, type };
        } else {
            this.currentSelection = { element: null, type: null };
        }
    }

    clearSelection() {
        document.querySelectorAll('.draggable-zone.selected, .draggable-rack.selected, .draggable-shelf.selected').forEach(el => {
            el.classList.remove('selected');
        });
        this.currentSelection = { element: null, type: null };
    }

    getSelectedElement() {
        if (this.currentSelection && this.currentSelection.element) {
            return this.currentSelection;
        }
        return null;
    }

    setupClipboardShortcuts() {
        if (this.clipboardShortcutsBound) {
            return;
        }
        document.addEventListener('keydown', this.boundClipboardHandler);
        this.clipboardShortcutsBound = true;
    }

    setupPointerTracking() {
        if (this.pointerTrackingBound) {
            return;
        }
        const updatePointer = (event) => {
            if (!event) return;
            this.pointerPosition = {
                clientX: event.clientX,
                clientY: event.clientY
            };
        };
        const resetPointer = () => {
            this.pointerPosition = null;
        };
        const container = this.svgContainer || this.svg || document;
        if (container) {
            container.addEventListener('mousemove', updatePointer);
            container.addEventListener('mouseleave', resetPointer);
            this.pointerTrackingBound = true;
        }
    }

    handleClipboardKeydown(event) {
        if (!event) {
            return;
        }
        const key = (event.key || '').toLowerCase();
        const isDeleteKey = key === 'delete' || key === 'backspace';
        if (!event.ctrlKey && !event.metaKey && isDeleteKey) {
            if (this.isEditableTarget(event.target)) {
                return;
            }
            const deleted = this.deleteCurrentSelection();
            if (deleted) {
                event.preventDefault();
            }
            return;
        }
        if (!event.ctrlKey && !event.metaKey) {
            return;
        }
        if (key !== 'c' && key !== 'v') {
            return;
        }
        if (this.isEditableTarget(event.target)) {
            return;
        }
        if (key === 'c') {
            const copied = this.copyCurrentSelection();
            if (copied) {
                event.preventDefault();
            }
        } else if (key === 'v') {
            const pasted = this.pasteFromClipboard();
            if (pasted) {
                event.preventDefault();
            }
        }
    }

    isEditableTarget(target) {
        if (!target) {
            return false;
        }
        const tagName = target.tagName ? target.tagName.toLowerCase() : '';
        const editableTags = ['input', 'textarea', 'select'];
        if (editableTags.includes(tagName) || target.isContentEditable) {
            return true;
        }
        return target.closest('[contenteditable="true"]') !== null;
    }

    copyCurrentSelection() {
        const selection = this.getSelectedElement();
        if (!selection || !selection.element) {
            console.warn('Brak zaznaczonego elementu do skopiowania.');
            return false;
        }
        const sourceId = this.getElementIdByType(selection.element, selection.type);
        if (!sourceId) {
            console.warn('Nie udało się ustawić schowka dla wybranego elementu.');
            return false;
        }
        this.clipboard = { type: selection.type, sourceId };
        console.info(`Skopiowano ${selection.type} #${sourceId} do schowka.`);
        const label = this.getEntityAccusativeLabel(selection.type);
        const name = this.getElementName(selection.element, selection.type);
        if (label) {
            this.showToast(`Skopiowano ${label}${name ? ` "${name}"` : ''}.`, 'info');
        } else {
            this.showToast(`Skopiowano element${name ? ` "${name}"` : ''}.`, 'info');
        }
        return true;
    }

    pasteFromClipboard() {
        if (!this.clipboard) {
            console.warn('Schowek jest pusty.');
            return false;
        }
        const selection = this.getSelectedElement();
        if (!selection || !selection.element) {
            console.warn('Wybierz element aby określić miejsce wklejenia.');
            return false;
        }
        if (selection.type !== this.clipboard.type) {
            console.warn('Typ zaznaczenia nie odpowiada zawartości schowka.');
            return false;
        }
        const pointerSnapshot = this.pointerPosition ? { ...this.pointerPosition } : null;
        const payload = this.calculatePastePayload(selection, pointerSnapshot);
        if (!payload) {
            console.warn('Nie udało się wyliczyć pozycji wklejenia.');
            return false;
        }

        if (selection.type === 'zone') {
            this.duplicateZoneRequest(this.clipboard.sourceId, payload, selection.element);
        } else if (selection.type === 'rack') {
            this.duplicateRackRequest(this.clipboard.sourceId, payload, selection.element);
        } else if (selection.type === 'shelf') {
            this.duplicateShelfRequest(this.clipboard.sourceId, payload, selection.element);
        }
        return true;
    }

    calculatePastePayload(selection, pointerPosition = null) {
        if (!selection || !selection.element) {
            return null;
        }
        if (selection.type === 'zone') {
            return this.calculateZonePastePayload(selection.element, pointerPosition);
        }
        if (selection.type === 'rack') {
            return this.calculateRackPastePayload(selection.element, pointerPosition);
        }
        if (selection.type === 'shelf') {
            return this.calculateShelfPastePayload(selection.element, pointerPosition);
        }
        return null;
    }

    calculateZonePastePayload(zoneGroup, pointerPosition = null) {
        const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
        if (!zoneMetrics) {
            return null;
        }
        const workspace = this.getWarehouseDimensions();
        const workspaceWidth = this.zoneMode.workspaceWidth || workspace.width || zoneMetrics.width;
        const workspaceHeight = this.zoneMode.workspaceHeight || workspace.height || zoneMetrics.height;
        if (pointerPosition) {
            const pointerActual = this.getPointerInWorkspaceActual(pointerPosition);
            if (pointerActual) {
                const maxX = Math.max(0, (workspaceWidth || zoneMetrics.width) - zoneMetrics.width);
                const maxY = Math.max(0, (workspaceHeight || zoneMetrics.height) - zoneMetrics.height);
                const clampedX = Math.min(Math.max(pointerActual.x - zoneMetrics.width / 2, 0), maxX);
                const clampedY = Math.min(Math.max(pointerActual.y - zoneMetrics.height / 2, 0), maxY);
                return {
                    x: clampedX,
                    y: clampedY
                };
            }
        }
        const { height: warehouseHeight } = this.getWarehouseDimensions();
        const desiredY = zoneMetrics.y + zoneMetrics.height + this.clipboardOffset;
        const maxY = Math.max(0, warehouseHeight - zoneMetrics.height);
        return {
            x: zoneMetrics.x,
            y: Math.min(desiredY, maxY)
        };
    }

    calculateRackPastePayload(rackGroup, pointerPosition = null) {
        const rackMetrics = this.getRackActualMetrics(rackGroup);
        const zoneGroup = rackGroup ? rackGroup.closest('.draggable-zone') : null;
        const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
        if (!rackMetrics || !zoneGroup || !zoneMetrics) {
            return null;
        }
        if (pointerPosition) {
            const placement = this.calculateRackCreationMetrics(zoneGroup, pointerPosition, {
                width: rackMetrics.width,
                height: rackMetrics.height,
                centerPointer: false
            });
            if (placement) {
                return {
                    x: placement.x,
                    y: placement.y,
                    zoneId: zoneGroup.getAttribute('data-zone-id')
                };
            }
        }
        const desiredY = rackMetrics.y + rackMetrics.height + this.clipboardOffset;
        const maxY = Math.max(0, zoneMetrics.height - rackMetrics.height);
        return {
            x: rackMetrics.x,
            y: Math.min(desiredY, maxY),
            zoneId: zoneGroup.getAttribute('data-zone-id')
        };
    }

    calculateShelfPastePayload(shelfGroup, pointerPosition = null) {
        if (!shelfGroup) {
            return null;
        }
        const rackGroup = shelfGroup.closest('.draggable-rack');
        const zoneGroup = rackGroup ? rackGroup.closest('.draggable-zone') : null;
        const rackMetrics = this.convertShelfMetricsForServer(
            shelfGroup,
            {
                x: parseFloat(shelfGroup.getAttribute('data-x')) || 0,
                y: parseFloat(shelfGroup.getAttribute('data-y')) || 0,
                width: parseFloat(shelfGroup.getAttribute('data-width')) || 0,
                height: parseFloat(shelfGroup.getAttribute('data-height')) || 0
            }
        );
        const rackActual = this.getRackActualMetrics(rackGroup);
        if (!rackMetrics || !rackGroup || !rackActual) {
            return null;
        }
        if (pointerPosition) {
            const placement = this.calculateShelfCreationMetrics(rackGroup, pointerPosition, {
                width: rackMetrics.width,
                height: rackMetrics.height,
                centerPointer: false
            });
            if (placement) {
                return {
                    x: placement.x,
                    y: placement.y,
                    rackId: rackGroup.getAttribute('data-rack-id'),
                    zoneId: zoneGroup ? zoneGroup.getAttribute('data-zone-id') : null
                };
            }
        }
        const desiredY = rackMetrics.y + rackMetrics.height + this.clipboardOffset;
        const maxY = Math.max(0, rackActual.height - rackMetrics.height);
        return {
            x: rackMetrics.x,
            y: Math.min(desiredY, maxY),
            rackId: rackGroup.getAttribute('data-rack-id'),
            zoneId: zoneGroup ? zoneGroup.getAttribute('data-zone-id') : null
        };
    }

    getZoneActualMetrics(zoneGroup) {
        if (!zoneGroup) {
            return null;
        }
        const workspaceMode = zoneGroup.dataset.workspaceMode === '1';
        const x = workspaceMode
            ? parseFloat(zoneGroup.dataset.zoneOriginalX) || 0
            : parseFloat(zoneGroup.getAttribute('data-x')) || 0;
        const y = workspaceMode
            ? parseFloat(zoneGroup.dataset.zoneOriginalY) || 0
            : parseFloat(zoneGroup.getAttribute('data-y')) || 0;
        const width = workspaceMode
            ? parseFloat(zoneGroup.dataset.zoneOriginalWidth) || parseFloat(zoneGroup.getAttribute('data-width')) || 0
            : parseFloat(zoneGroup.getAttribute('data-width')) || 0;
        const height = workspaceMode
            ? parseFloat(zoneGroup.dataset.zoneOriginalHeight) || parseFloat(zoneGroup.getAttribute('data-height')) || 0
            : parseFloat(zoneGroup.getAttribute('data-height')) || 0;
        return { x, y, width, height, workspaceMode };
    }

    getRackActualMetrics(rackGroup) {
        if (!rackGroup) {
            return null;
        }
        const rackWorkspaceMode = rackGroup.dataset.rackWorkspaceMode === '1';
        const zoneWorkspaceMode = rackGroup.dataset.zoneWorkspaceMode === '1';
        if (rackWorkspaceMode) {
            const x = parseFloat(rackGroup.dataset.rackDetailOriginalX) || 0;
            const y = parseFloat(rackGroup.dataset.rackDetailOriginalY) || 0;
            const width = parseFloat(rackGroup.dataset.rackDetailOriginalWidth) || parseFloat(rackGroup.getAttribute('data-width')) || 0;
            const height = parseFloat(rackGroup.dataset.rackDetailOriginalHeight) || parseFloat(rackGroup.getAttribute('data-height')) || 0;
            return { x, y, width, height, workspaceMode: true };
        }
        if (zoneWorkspaceMode) {
            const x = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalX) || 0;
            const y = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalY) || 0;
            const width = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalWidth) || 0;
            const height = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalHeight) || 0;
            return { x, y, width, height, workspaceMode: true };
        }
        const x = parseFloat(rackGroup.getAttribute('data-x')) || 0;
        const y = parseFloat(rackGroup.getAttribute('data-y')) || 0;
        const width = parseFloat(rackGroup.getAttribute('data-width')) || 0;
        const height = parseFloat(rackGroup.getAttribute('data-height')) || 0;
        return { x, y, width, height, workspaceMode: false };
    }

    getWarehouseDimensions() {
        if (!this.svg) {
            return { width: 0, height: 0 };
        }
        const viewBoxAttr = this.svg.getAttribute('viewBox');
        if (!viewBoxAttr) {
            return { width: 0, height: 0 };
        }
        const parts = viewBoxAttr.split(' ').map(parseFloat);
        return {
            width: parts[2] || 0,
            height: parts[3] || 0
        };
    }

    getSvgCoordinatesFromClient(clientX, clientY) {
        if (!this.svg || typeof clientX !== 'number' || typeof clientY !== 'number') {
            return null;
        }
        const point = this.svg.createSVGPoint();
        point.x = clientX;
        point.y = clientY;
        const ctm = this.svg.getScreenCTM();
        if (!ctm) {
            return null;
        }
        const transformed = point.matrixTransform(ctm.inverse());
        return { x: transformed.x, y: transformed.y };
    }

    getPointerRelativeToZoneDisplay(zoneGroup, pointerPosition) {
        if (!zoneGroup || !pointerPosition) {
            return null;
        }
        const svgCoords = this.getSvgCoordinatesFromClient(pointerPosition.clientX, pointerPosition.clientY);
        if (!svgCoords) {
            return null;
        }
        const zoneDisplayX = parseFloat(zoneGroup.getAttribute('data-x')) || 0;
        const zoneDisplayY = parseFloat(zoneGroup.getAttribute('data-y')) || 0;
        return {
            x: svgCoords.x - zoneDisplayX,
            y: svgCoords.y - zoneDisplayY
        };
    }

    convertZoneDisplayToActual(zoneGroup, displayCoord) {
        if (!zoneGroup || !displayCoord) {
            return null;
        }
        const workspaceMode = zoneGroup.dataset.workspaceMode === '1';
        if (!workspaceMode) {
            return displayCoord;
        }
        const workspaceWidth = parseFloat(zoneGroup.getAttribute('data-width')) || 1;
        const workspaceHeight = parseFloat(zoneGroup.getAttribute('data-height')) || 1;
        const zoneWidth = parseFloat(zoneGroup.dataset.zoneOriginalWidth) || workspaceWidth;
        const zoneHeight = parseFloat(zoneGroup.dataset.zoneOriginalHeight) || workspaceHeight;
        return {
            x: workspaceWidth ? (displayCoord.x / workspaceWidth) * zoneWidth : displayCoord.x,
            y: workspaceHeight ? (displayCoord.y / workspaceHeight) * zoneHeight : displayCoord.y
        };
    }

    getPointerInZoneActual(zoneGroup, pointerPosition) {
        const displayCoords = this.getPointerRelativeToZoneDisplay(zoneGroup, pointerPosition);
        if (!displayCoords) {
            return null;
        }
        return this.convertZoneDisplayToActual(zoneGroup, displayCoords);
    }

    getPointerInWorkspaceActual(pointerPosition) {
        if (!pointerPosition) {
            return null;
        }
        const svgCoords = this.getSvgCoordinatesFromClient(pointerPosition.clientX, pointerPosition.clientY);
        if (!svgCoords) {
            return null;
        }
        const activeZoneId = this.zoneMode && this.zoneMode.activeZoneId;
        if (!activeZoneId) {
            return svgCoords;
        }
        const zoneGroup = this.getZoneGroupById(activeZoneId);
        if (!zoneGroup) {
            return svgCoords;
        }
        const pointerInZone = this.getPointerInZoneActual(zoneGroup, pointerPosition);
        if (!pointerInZone) {
            return svgCoords;
        }
        return pointerInZone;
    }

    calculateZoneCreationMetrics(clientPosition) {
        const workspace = this.getWarehouseDimensions();
        const defaults = (this.defaultSizes && this.defaultSizes.zone) || { width: 200, height: 150 };
        const defaultWidth = Number(defaults.width) || 200;
        const defaultHeight = Number(defaults.height) || 150;
        const workspaceWidth = this.zoneMode.workspaceWidth || workspace.width || defaultWidth;
        const workspaceHeight = this.zoneMode.workspaceHeight || workspace.height || defaultHeight;
        let targetX = 0;
        let targetY = 0;
        if (clientPosition) {
            const svgCoords = this.getSvgCoordinatesFromClient(clientPosition.clientX, clientPosition.clientY);
            if (svgCoords) {
                targetX = svgCoords.x;
                targetY = svgCoords.y;
            }
        }
        const maxX = Math.max(0, workspaceWidth - defaultWidth);
        const maxY = Math.max(0, workspaceHeight - defaultHeight);
        const clampedX = Math.min(Math.max(targetX, 0), maxX);
        const clampedY = Math.min(Math.max(targetY, 0), maxY);
        return {
            x: clampedX,
            y: clampedY,
            width: defaultWidth,
            height: defaultHeight,
            color: (this.defaultColors && this.defaultColors.zone) || '#007bff',
            name: null
        };
    }

    calculateRackCreationMetrics(zoneGroup, clientPosition, overrides = {}) {
        if (!zoneGroup) return null;
        const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
        if (!zoneMetrics) return null;
        const defaults = (this.defaultSizes && this.defaultSizes.rack) || { width: 80, height: 60 };
        const width = typeof overrides.width === 'number' ? overrides.width : (Number(defaults.width) || 80);
        const height = typeof overrides.height === 'number' ? overrides.height : (Number(defaults.height) || 60);
        const centerPointer = overrides.centerPointer !== false;
        let relativeX = 0;
        let relativeY = 0;
        const pointerActual = this.getPointerInZoneActual(zoneGroup, clientPosition);
        if (pointerActual) {
            relativeX = pointerActual.x - (centerPointer ? width / 2 : 0);
            relativeY = pointerActual.y - (centerPointer ? height / 2 : 0);
        } else {
            relativeX = (zoneMetrics.width - width) / 2;
            relativeY = (zoneMetrics.height - height) / 2;
        }
        const maxX = Math.max(0, zoneMetrics.width - width);
        const maxY = Math.max(0, zoneMetrics.height - height);
        const clampedX = Math.min(Math.max(relativeX, 0), maxX);
        const clampedY = Math.min(Math.max(relativeY, 0), maxY);
        return {
            x: clampedX,
            y: clampedY,
            width,
            height,
            color: overrides.color || (this.defaultColors && this.defaultColors.rack) || '#28a745',
            name: overrides.name || null
        };
    }

    calculateShelfCreationMetrics(rackGroup, clientPosition, overrides = {}) {
        if (!rackGroup) return null;
        const rackMetrics = this.getRackActualMetrics(rackGroup);
        if (!rackMetrics) return null;
        const zoneGroup = rackGroup.closest('.draggable-zone');
        const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
        if (!zoneMetrics) return null;
        const defaults = (this.defaultSizes && this.defaultSizes.shelf) || { width: 60, height: 20 };
        const width = typeof overrides.width === 'number' ? overrides.width : (Number(defaults.width) || 60);
        const height = typeof overrides.height === 'number' ? overrides.height : (Number(defaults.height) || 20);
        const centerPointer = overrides.centerPointer !== false;
        let relativeX = 0;
        let relativeY = 0;
        const pointerActual = this.getPointerInZoneActual(zoneGroup, clientPosition);
        if (pointerActual) {
            relativeX = pointerActual.x - rackMetrics.x - (centerPointer ? width / 2 : 0);
            relativeY = pointerActual.y - rackMetrics.y - (centerPointer ? height / 2 : 0);
        } else {
            relativeX = (rackMetrics.width - width) / 2;
            relativeY = (rackMetrics.height - height) / 2;
        }
        const maxX = Math.max(0, rackMetrics.width - width);
        const maxY = Math.max(0, rackMetrics.height - height);
        const clampedX = Math.min(Math.max(relativeX, 0), maxX);
        const clampedY = Math.min(Math.max(relativeY, 0), maxY);
        return {
            x: clampedX,
            y: clampedY,
            width,
            height,
            color: overrides.color || (this.defaultColors && this.defaultColors.shelf) || '#ffc107',
            name: overrides.name || null
        };
    }

    deleteCurrentSelection() {
        const selection = this.getSelectedElement();
        if (!selection || !selection.element || !selection.type) {
            return false;
        }
        if (selection.type === 'zone') {
            this.deleteZone(selection.element);
            return true;
        }
        if (selection.type === 'rack') {
            this.deleteRack(selection.element);
            return true;
        }
        if (selection.type === 'shelf') {
            this.deleteShelf(selection.element);
            return true;
        }
        return false;
    }

    deleteZone(zoneGroup) {
        if (!zoneGroup) {
            return;
        }
        const zoneId = zoneGroup.getAttribute('data-zone-id');
        if (!zoneId) {
            return;
        }
        this.performDeleteRequest(`/wms-builder/zones/${zoneId}/delete/`, {
            onSuccess: () => {
                zoneGroup.remove();
                if (this.zoneMode.activeZoneId === zoneId) {
                    this.setZoneMode(null);
                }
                if (this.zoneModeSelect) {
                    const option = this.zoneModeSelect.querySelector(`option[value="${zoneId}"]`);
                    if (option) {
                        option.remove();
                    }
                }
                this.clearSelection();
                if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                    this.zoneMode.updateZonesVisibility();
                }
            },
            successMessage: 'Strefa została usunięta.',
            errorMessage: 'Nie udało się usunąć strefy.'
        });
    }

    deleteRack(rackGroup) {
        if (!rackGroup) {
            return;
        }
        const rackId = rackGroup.getAttribute('data-rack-id');
        if (!rackId) {
            return;
        }
        
        // Sprawdź czy jesteśmy w widoku tego regału
        const isInRackDetailView = this.rackMode.activeRackId === rackId;
        const zoneId = rackGroup.closest('.draggable-zone')?.getAttribute('data-zone-id');
        
        this.performDeleteRequest(`/wms-builder/racks/${rackId}/delete/`, {
            onSuccess: () => {
                rackGroup.remove();
                if (isInRackDetailView && zoneId) {
                    // Jeśli jesteśmy w widoku szczegółowym tego regału, przekieruj do widoku strefy
                    // Zapisuj toast w sessionStorage przed przekierowaniem
                    if (typeof htmx !== 'undefined') {
                        htmx.trigger(document.body, 'toastMessage', {
                            value: 'Regał został usunięty. Zostałeś przekierowany do widoku strefy.',
                            type: 'info'
                        });
                        sessionStorage.setItem('deleteToast', JSON.stringify({
                            value: 'Regał został usunięty. Zostałeś przekierowany do widoku strefy.',
                            type: 'info'
                        }));
                    }
                    // Przekieruj do widoku strefy
                    window.location.href = `/wms-builder/warehouses/${this.warehouseId}/zones/${zoneId}/?not_found=rack`;
                    return;
                }
                if (this.rackMode.activeRackId === rackId) {
                    this.setRackMode(null);
                }
                this.clearSelection();
                if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                    this.zoneMode.updateZonesVisibility();
                }
            },
            successMessage: 'Regał został usunięty.',
            errorMessage: 'Nie udało się usunąć regału.'
        });
    }

    deleteShelf(shelfGroup) {
        if (!shelfGroup) {
            return;
        }
        const shelfId = shelfGroup.getAttribute('data-shelf-id');
        if (!shelfId) {
            return;
        }
        
        // Sprawdź czy jesteśmy w widoku regału, który zawiera tę półkę
        const rackGroup = shelfGroup.closest('.draggable-rack');
        const rackId = rackGroup ? rackGroup.getAttribute('data-rack-id') : null;
        const isInRackDetailView = rackId && this.rackMode.activeRackId === rackId;
        const zoneId = rackGroup ? rackGroup.closest('.draggable-zone')?.getAttribute('data-zone-id') : null;
        
        this.performDeleteRequest(`/wms-builder/shelves/${shelfId}/delete/`, {
            onSuccess: () => {
                shelfGroup.remove();
                if (isInRackDetailView && zoneId && rackId) {
                    // Jeśli jesteśmy w widoku szczegółowym regału, który zawiera tę półkę, 
                    // przekieruj do widoku regału (półka już została usunięta)
                    // Zapisuj toast w sessionStorage przed przekierowaniem
                    if (typeof htmx !== 'undefined') {
                        htmx.trigger(document.body, 'toastMessage', {
                            value: 'Półka została usunięta. Zostałeś przekierowany do widoku regału.',
                            type: 'info'
                        });
                        sessionStorage.setItem('deleteToast', JSON.stringify({
                            value: 'Półka została usunięta. Zostałeś przekierowany do widoku regału.',
                            type: 'info'
                        }));
                    }
                    // Przekieruj do widoku regału
                    window.location.href = `/wms-builder/warehouses/${this.warehouseId}/zones/${zoneId}/racks/${rackId}/?not_found=shelf`;
                    return;
                }
                this.clearSelection();
            },
            successMessage: 'Półka została usunięta.',
            errorMessage: 'Nie udało się usunąć półki.'
        });
    }

    performDeleteRequest(url, options = {}) {
        if (!url) {
            return;
        }
        const { onSuccess, successMessage, errorMessage } = options;
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            }
        }).then(response => {
            // Odczytaj HX-Trigger header i wywołaj eventy (dla wszystkich statusów)
            const triggerHeader = response.headers.get('HX-Trigger');
            console.log('Delete response status:', response.status);
            console.log('HX-Trigger header:', triggerHeader);
            if (triggerHeader && typeof htmx !== 'undefined') {
                try {
                    const triggers = JSON.parse(triggerHeader);
                    console.log('Parsed triggers:', triggers);
                    // Obsługa toastMessage (pojedynczy lub lista)
                    if (triggers.toastMessage) {
                        console.log('Triggering toastMessage:', triggers.toastMessage);
                        htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                    }
                    if (triggers.toastMessageList) {
                        console.log('Triggering toastMessageList:', triggers.toastMessageList);
                        htmx.trigger(document.body, 'toastMessageList', triggers.toastMessageList);
                    }
                } catch (e) {
                    console.error('Error parsing HX-Trigger:', e, triggerHeader);
                }
            } else {
                console.warn('No HX-Trigger header or htmx not available');
            }
            
            if (response.status === 204) {
                if (typeof onSuccess === 'function') {
                    onSuccess();
                }
                // Jeśli successMessage jest podany jako fallback (dla kompatybilności wstecznej)
                if (successMessage && !triggerHeader && typeof htmx !== 'undefined') {
                    htmx.trigger(document.body, 'toastMessage', {
                        value: successMessage,
                        type: 'success'
                    });
                }
            } else if (response.status === 400) {
                // Status 400 - błąd walidacji, toast message już został wyświetlony przez HX-Trigger
                // Nie wywołuj onSuccess i nie rzucaj błędu
                return;
            } else if (!response.ok) {
                throw new Error(`Delete request failed: ${url}`);
            }
        }).catch(error => {
            console.error(error);
            // Wyświetl ogólny komunikat błędu tylko jeśli nie było HX-Trigger
            if (errorMessage && typeof htmx !== 'undefined') {
                htmx.trigger(document.body, 'toastMessage', {
                    value: errorMessage,
                    type: 'danger'
                });
            }
        });
    }

    duplicateZoneRequest(sourceZoneId, payload, referenceZone) {
        if (!sourceZoneId || !payload) {
            return;
        }
        const formData = new FormData();
        formData.append('x', payload.x);
        formData.append('y', payload.y);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/zones/${sourceZoneId}/duplicate/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error('Nie udało się zduplikować strefy.');
            }
            return response.json();
        }).then(data => {
            if (!data || !data.zone) {
                return;
            }
            const zoneGroup = this.createZoneElement(data.zone);
            if (!zoneGroup) {
                return;
            }
            this.insertAfter(zoneGroup, referenceZone);
            const zoneRect = zoneGroup.querySelector('.zone-rect');
            if (zoneRect) {
                this.bindZoneSelectionHandlers(zoneRect);
            }
            zoneGroup.querySelectorAll('.draggable-rack').forEach(rack => {
                this.bindRackSelectionHandlers(rack);
                this.applyRackWorkspaceTransformIfNeeded(rack);
                rack.querySelectorAll('.draggable-shelf').forEach(shelf => {
                    this.bindShelfSelectionHandlers(shelf);
                    this.applyShelfWorkspaceTransformIfNeeded(shelf);
                });
            });
            this.setSelection(zoneGroup, 'zone');
            if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                this.zoneMode.updateZonesVisibility();
            }
            const label = this.getEntityAccusativeLabel('zone');
            const name = data.zone && data.zone.name ? data.zone.name : null;
            this.showToast(`Wklejono ${label || 'element'}${name ? ` "${name}"` : ''}.`, 'success');
        }).catch(error => {
            console.error(error);
        });
    }

    duplicateRackRequest(sourceRackId, payload, referenceRack) {
        if (!sourceRackId || !payload || !payload.zoneId) {
            return;
        }
        const formData = new FormData();
        formData.append('x', payload.x);
        formData.append('y', payload.y);
        formData.append('target_zone_id', payload.zoneId);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/racks/${sourceRackId}/duplicate/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error('Nie udało się zduplikować regału.');
            }
            return response.json();
        }).then(data => {
            if (!data || !data.rack) {
                return;
            }
            const zoneGroup = this.getZoneGroupById(payload.zoneId);
            const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
            if (!zoneGroup || !zoneMetrics) {
                return;
            }
            const rackGroup = this.createRackElement(data.rack, zoneMetrics);
            if (!rackGroup) {
                return;
            }
            this.insertAfter(rackGroup, referenceRack);
            this.bindRackSelectionHandlers(rackGroup);
            rackGroup.querySelectorAll('.draggable-shelf').forEach(shelf => {
                this.bindShelfSelectionHandlers(shelf);
                this.applyShelfWorkspaceTransformIfNeeded(shelf);
            });
            this.applyRackWorkspaceTransformIfNeeded(rackGroup);
            this.setSelection(rackGroup, 'rack');
        const label = this.getEntityAccusativeLabel('rack');
        const name = data && data.rack && data.rack.name ? data.rack.name : null;
        this.showToast(`Wklejono ${label || 'element'}${name ? ` "${name}"` : ''}.`, 'success');
        }).catch(error => {
            console.error(error);
        });
    }

    duplicateShelfRequest(sourceShelfId, payload, referenceShelf) {
        if (!sourceShelfId || !payload || !payload.rackId) {
            return;
        }
        const formData = new FormData();
        formData.append('x', payload.x);
        formData.append('y', payload.y);
        formData.append('target_rack_id', payload.rackId);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        fetch(`/wms-builder/shelves/${sourceShelfId}/duplicate/`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error('Nie udało się zduplikować półki.');
            }
            return response.json();
        }).then(data => {
            if (!data || !data.shelf) {
                return;
            }
            const rackGroup = this.getRackGroupById(payload.rackId);
            const zoneGroup = rackGroup ? rackGroup.closest('.draggable-zone') : null;
            const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
            const rackMetrics = this.getRackActualMetrics(rackGroup);
            if (!rackGroup || !zoneMetrics || !rackMetrics) {
                return;
            }
            const shelfGroup = this.createShelfElement(data.shelf, {
                zoneX: zoneMetrics.x,
                zoneY: zoneMetrics.y,
                rackX: rackMetrics.x,
                rackY: rackMetrics.y
            });
            if (!shelfGroup) {
                return;
            }
            this.insertAfter(shelfGroup, referenceShelf);
            this.bindShelfSelectionHandlers(shelfGroup);
            this.applyShelfWorkspaceTransformIfNeeded(shelfGroup);
            this.setSelection(shelfGroup, 'shelf');
            const label = this.getEntityAccusativeLabel('shelf');
            const name = data.shelf && data.shelf.name ? data.shelf.name : null;
            this.showToast(`Wklejono ${label || 'element'}${name ? ` "${name}"` : ''}.`, 'success');
        }).catch(error => {
            console.error(error);
        });
    }

    createZoneElement(zoneData) {
        if (!zoneData) {
            return null;
        }
        const zoneGroup = this.createSvgElement('g');
        zoneGroup.id = `zone-${zoneData.id}`;
        zoneGroup.classList.add('draggable-zone');
        zoneGroup.setAttribute('data-zone-id', zoneData.id);
        zoneGroup.setAttribute('data-x', zoneData.x);
        zoneGroup.setAttribute('data-y', zoneData.y);
        zoneGroup.setAttribute('data-width', zoneData.width);
        zoneGroup.setAttribute('data-height', zoneData.height);
        if (zoneData.synced) {
            zoneGroup.setAttribute('data-synced', 'true');
        }

        const rect = this.createSvgElement('rect');
        rect.setAttribute('x', zoneData.x);
        rect.setAttribute('y', zoneData.y);
        rect.setAttribute('width', zoneData.width);
        rect.setAttribute('height', zoneData.height);
        rect.setAttribute('fill', zoneData.color || '#007bff');
        rect.setAttribute('fill-opacity', '0.3');
        rect.setAttribute('stroke', zoneData.color || '#007bff');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('rx', '5');
        rect.classList.add('zone-rect');
        zoneGroup.appendChild(rect);

        const handle = this.createSvgElement('circle');
        handle.setAttribute('cx', zoneData.x + zoneData.width);
        handle.setAttribute('cy', zoneData.y + zoneData.height);
        handle.setAttribute('r', '5');
        handle.setAttribute('fill', zoneData.color || '#007bff');
        handle.setAttribute('stroke', 'white');
        handle.setAttribute('stroke-width', '2');
        handle.classList.add('resize-handle-indicator');
        zoneGroup.appendChild(handle);

        const text = this.createSvgElement('text');
        text.setAttribute('x', zoneData.x + zoneData.width / 2);
        text.setAttribute('y', zoneData.y + zoneData.height / 2);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '14');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', '#333');
        text.textContent = zoneData.name || '';
        zoneGroup.appendChild(text);

        if (zoneData.synced) {
            const syncIndicator = this.createSvgElement('circle');
            syncIndicator.setAttribute('cx', zoneData.x + zoneData.width - 10);
            syncIndicator.setAttribute('cy', zoneData.y + 10);
            syncIndicator.setAttribute('r', '6');
            syncIndicator.setAttribute('fill', '#28a745');
            syncIndicator.setAttribute('stroke', 'white');
            syncIndicator.setAttribute('stroke-width', '1.5');
            syncIndicator.classList.add('zone-sync-indicator');
            zoneGroup.appendChild(syncIndicator);
        }

        if (Array.isArray(zoneData.racks)) {
            zoneData.racks.forEach(rackData => {
                const rackGroup = this.createRackElement(rackData, zoneData);
                if (rackGroup) {
                    zoneGroup.appendChild(rackGroup);
                }
            });
        }

        return zoneGroup;
    }

    createRackElement(rackData, zoneContext) {
        if (!rackData || !zoneContext) {
            return null;
        }
        const zoneX = zoneContext.x || 0;
        const zoneY = zoneContext.y || 0;
        const rackGroup = this.createSvgElement('g');
        rackGroup.id = `rack-${rackData.id}`;
        rackGroup.classList.add('draggable-rack');
        rackGroup.setAttribute('data-rack-id', rackData.id);
        rackGroup.setAttribute('data-x', rackData.x);
        rackGroup.setAttribute('data-y', rackData.y);
        rackGroup.setAttribute('data-width', rackData.width);
        rackGroup.setAttribute('data-height', rackData.height);
        if (rackData.synced) {
            rackGroup.setAttribute('data-synced', 'true');
        }

        const absX = zoneX + rackData.x;
        const absY = zoneY + rackData.y;

        const rect = this.createSvgElement('rect');
        rect.setAttribute('x', absX);
        rect.setAttribute('y', absY);
        rect.setAttribute('width', rackData.width);
        rect.setAttribute('height', rackData.height);
        rect.setAttribute('fill', rackData.color || '#28a745');
        rect.setAttribute('fill-opacity', '0.5');
        rect.setAttribute('stroke', rackData.color || '#28a745');
        rect.setAttribute('stroke-width', '1.5');
        rect.setAttribute('rx', '3');
        rect.classList.add('rack-rect');
        rackGroup.appendChild(rect);

        const handle = this.createSvgElement('circle');
        handle.setAttribute('cx', absX + rackData.width);
        handle.setAttribute('cy', absY + rackData.height);
        handle.setAttribute('r', '4');
        handle.setAttribute('fill', rackData.color || '#28a745');
        handle.setAttribute('stroke', 'white');
        handle.setAttribute('stroke-width', '1.5');
        handle.classList.add('resize-handle-indicator');
        rackGroup.appendChild(handle);

        const text = this.createSvgElement('text');
        text.setAttribute('x', absX + rackData.width / 2);
        text.setAttribute('y', absY + rackData.height / 2);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '10');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', '#333');
        text.textContent = rackData.name || '';
        rackGroup.appendChild(text);

        if (rackData.synced) {
            const syncIndicator = this.createSvgElement('circle');
            syncIndicator.setAttribute('cx', absX + rackData.width - 8);
            syncIndicator.setAttribute('cy', absY + 8);
            syncIndicator.setAttribute('r', '5');
            syncIndicator.setAttribute('fill', '#28a745');
            syncIndicator.setAttribute('stroke', 'white');
            syncIndicator.setAttribute('stroke-width', '1');
            syncIndicator.classList.add('rack-sync-indicator');
            rackGroup.appendChild(syncIndicator);
        }

        if (Array.isArray(rackData.shelves)) {
            rackData.shelves.forEach(shelfData => {
                const shelfGroup = this.createShelfElement(shelfData, {
                    zoneX,
                    zoneY,
                    rackX: rackData.x,
                    rackY: rackData.y
                });
                if (shelfGroup) {
                    rackGroup.appendChild(shelfGroup);
                }
            });
        }

        return rackGroup;
    }

    createShelfElement(shelfData, context) {
        if (!shelfData || !context) {
            return null;
        }
        const zoneX = context.zoneX || 0;
        const zoneY = context.zoneY || 0;
        const rackX = context.rackX || 0;
        const rackY = context.rackY || 0;
        const group = this.createSvgElement('g');
        group.id = `shelf-${shelfData.id}`;
        group.classList.add('draggable-shelf');
        group.setAttribute('data-shelf-id', shelfData.id);
        group.setAttribute('data-x', shelfData.x);
        group.setAttribute('data-y', shelfData.y);
        group.setAttribute('data-width', shelfData.width);
        group.setAttribute('data-height', shelfData.height);
        if (shelfData.synced) {
            group.setAttribute('data-synced', 'true');
        }

        const absX = zoneX + rackX + shelfData.x;
        const absY = zoneY + rackY + shelfData.y;

        const rect = this.createSvgElement('rect');
        rect.setAttribute('x', absX);
        rect.setAttribute('y', absY);
        rect.setAttribute('width', shelfData.width);
        rect.setAttribute('height', shelfData.height);
        rect.setAttribute('fill', shelfData.color || '#ffc107');
        rect.setAttribute('fill-opacity', '0.7');
        rect.setAttribute('stroke', shelfData.color || '#ffc107');
        rect.setAttribute('stroke-width', '1');
        rect.setAttribute('rx', '2');
        rect.classList.add('shelf-rect');
        group.appendChild(rect);

        const handle = this.createSvgElement('circle');
        handle.setAttribute('cx', absX + shelfData.width);
        handle.setAttribute('cy', absY + shelfData.height);
        handle.setAttribute('r', '3');
        handle.setAttribute('fill', shelfData.color || '#ffc107');
        handle.setAttribute('stroke', 'white');
        handle.setAttribute('stroke-width', '1');
        handle.classList.add('resize-handle-indicator');
        group.appendChild(handle);

        const text = this.createSvgElement('text');
        text.setAttribute('x', absX + shelfData.width / 2);
        text.setAttribute('y', absY + shelfData.height / 2);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '8');
        text.setAttribute('fill', '#333');
        text.textContent = this.truncateLabel(shelfData.name || '', 5);
        group.appendChild(text);

        if (shelfData.synced) {
            const syncIndicator = this.createSvgElement('circle');
            syncIndicator.setAttribute('cx', absX + shelfData.width - 6);
            syncIndicator.setAttribute('cy', absY + 6);
            syncIndicator.setAttribute('r', '4');
            syncIndicator.setAttribute('fill', '#28a745');
            syncIndicator.setAttribute('stroke', 'white');
            syncIndicator.setAttribute('stroke-width', '1');
            group.appendChild(syncIndicator);
        }

        return group;
    }

    insertAfter(newElement, referenceElement) {
        if (!newElement) {
            return;
        }
        const parent = referenceElement && referenceElement.parentNode ? referenceElement.parentNode : (this.svg || null);
        if (!parent) {
            return;
        }
        if (referenceElement && referenceElement.nextSibling) {
            parent.insertBefore(newElement, referenceElement.nextSibling);
        } else {
            parent.appendChild(newElement);
        }
    }

    applyRackWorkspaceTransformIfNeeded(rackGroup) {
        if (!rackGroup) {
            return;
        }
        if (rackGroup.dataset.zoneWorkspaceMode === '1') {
            return;
        }
        const zoneGroup = rackGroup.closest('.draggable-zone');
        if (!zoneGroup || zoneGroup.dataset.workspaceMode !== '1') {
            return;
        }
        const zoneWidth = parseFloat(zoneGroup.dataset.zoneOriginalWidth) || parseFloat(zoneGroup.getAttribute('data-width')) || 0;
        const zoneHeight = parseFloat(zoneGroup.dataset.zoneOriginalHeight) || parseFloat(zoneGroup.getAttribute('data-height')) || 0;
        const workspaceWidth = parseFloat(zoneGroup.dataset.workspaceWidth) || parseFloat(zoneGroup.getAttribute('data-width')) || zoneWidth;
        const workspaceHeight = parseFloat(zoneGroup.dataset.workspaceHeight) || parseFloat(zoneGroup.getAttribute('data-height')) || zoneHeight;
        this.convertRackToWorkspace(rackGroup, zoneWidth, zoneHeight, workspaceWidth, workspaceHeight);
    }

    applyShelfWorkspaceTransformIfNeeded(shelfGroup) {
        if (!shelfGroup) {
            return;
        }
        const rackGroup = shelfGroup.closest('.draggable-rack');
        if (!rackGroup) {
            return;
        }
        if (rackGroup.dataset.rackWorkspaceMode === '1') {
            const rackWidth =
                parseFloat(rackGroup.dataset.rackDetailZoneWidth) ||
                parseFloat(rackGroup.dataset.rackDetailOriginalWidth) ||
                parseFloat(rackGroup.getAttribute('data-width')) ||
                0;
            const rackHeight =
                parseFloat(rackGroup.dataset.rackDetailZoneHeight) ||
                parseFloat(rackGroup.dataset.rackDetailOriginalHeight) ||
                parseFloat(rackGroup.getAttribute('data-height')) ||
                0;
            const workspaceWidth = parseFloat(rackGroup.dataset.rackDetailWorkspaceWidth) || parseFloat(rackGroup.getAttribute('data-width')) || rackWidth;
            const workspaceHeight = parseFloat(rackGroup.dataset.rackDetailWorkspaceHeight) || parseFloat(rackGroup.getAttribute('data-height')) || rackHeight;
            const rackX = parseFloat(rackGroup.getAttribute('data-x')) || 0;
            const rackY = parseFloat(rackGroup.getAttribute('data-y')) || 0;
            this.convertShelfToWorkspace(shelfGroup, rackWidth, rackHeight, workspaceWidth, workspaceHeight, rackX, rackY);
            return;
        }

        if (rackGroup.dataset.zoneWorkspaceMode === '1') {
            const rackWidth = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalWidth) || 0;
            const rackHeight = parseFloat(rackGroup.dataset.zoneWorkspaceOriginalHeight) || 0;
            const workspaceWidth = parseFloat(rackGroup.dataset.zoneWorkspaceWidth) || parseFloat(rackGroup.getAttribute('data-width')) || rackWidth;
            const workspaceHeight = parseFloat(rackGroup.dataset.zoneWorkspaceHeight) || parseFloat(rackGroup.getAttribute('data-height')) || rackHeight;
            const rackX = parseFloat(rackGroup.getAttribute('data-x')) || 0;
            const rackY = parseFloat(rackGroup.getAttribute('data-y')) || 0;
            this.convertShelfToWorkspace(shelfGroup, rackWidth, rackHeight, workspaceWidth, workspaceHeight, rackX, rackY);
        }
    }

    createSvgElement(tagName) {
        return document.createElementNS('http://www.w3.org/2000/svg', tagName);
    }

    truncateLabel(label, maxLength = 5) {
        if (!label) {
            return '';
        }
        if (label.length <= maxLength) {
            return label;
        }
        return `${label.substring(0, maxLength)}…`;
    }

    getElementIdByType(element, type) {
        if (!element) {
            return null;
        }
        if (type === 'zone') {
            return element.getAttribute('data-zone-id');
        }
        if (type === 'rack') {
            return element.getAttribute('data-rack-id');
        }
        if (type === 'shelf') {
            return element.getAttribute('data-shelf-id');
        }
        return null;
    }

    formatNumber(value) {
        if (typeof value !== 'number' || Number.isNaN(value) || !Number.isFinite(value)) {
            return '0';
        }
        return value.toFixed(2);
    }

    getElementName(element, type) {
        if (!element) {
            return null;
        }
        if (type === 'zone') {
            const zoneText = element.querySelector('text');
            return zoneText ? zoneText.textContent.trim() : null;
        }
        if (type === 'rack') {
            const rackText = element.querySelector('text');
            return rackText ? rackText.textContent.trim() : null;
        }
        if (type === 'shelf') {
            const shelfText = element.querySelector('text');
            return shelfText ? shelfText.textContent.trim() : null;
        }
        return null;
    }

    getEntityAccusativeLabel(type) {
        switch (type) {
            case 'zone':
                return 'strefę';
            case 'rack':
                return 'regał';
            case 'shelf':
                return 'półkę';
            default:
                return null;
        }
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
        
        const createZoneAtPosition = (clientPosition = null) => {
            if (!warehouseId) {
                console.error('Warehouse ID is missing, cannot create zone.');
                return;
            }
            const metrics = this.calculateZoneCreationMetrics(clientPosition);
            if (!metrics) {
                return;
            }
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCsrfToken());
            formData.append('x', this.formatNumber(metrics.x));
            formData.append('y', this.formatNumber(metrics.y));
            formData.append('width', this.formatNumber(metrics.width));
            formData.append('height', this.formatNumber(metrics.height));
            formData.append('color', metrics.color);
            if (metrics.name) {
                formData.append('name', metrics.name);
            }
            fetch(`/wms-builder/warehouses/${warehouseId}/zones/quick-create/`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Nie udało się utworzyć strefy.');
                }
                return response.json();
            }).then(data => {
                if (!data || !data.zone) {
                    return;
                }
                const zoneGroup = this.createZoneElement(data.zone);
                if (!zoneGroup) {
                    return;
                }
                this.svg.appendChild(zoneGroup);
                const zoneRect = zoneGroup.querySelector('.zone-rect');
                if (zoneRect) {
                    this.bindZoneSelectionHandlers(zoneRect);
                }
                zoneGroup.querySelectorAll('.draggable-rack').forEach(rack => {
                    this.bindRackSelectionHandlers(rack);
                });
                this.setSelection(zoneGroup, 'zone');
                if (this.zoneModeSelect) {
                    const option = document.createElement('option');
                    option.value = data.zone.id;
                    option.textContent = `Widok: ${data.zone.name}`;
                    this.zoneModeSelect.appendChild(option);
                }
                if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                    this.zoneMode.updateZonesVisibility();
                }
                const label = this.getEntityAccusativeLabel('zone');
                this.showToast(`Dodano ${label || 'strefę'} "${data.zone.name}".`, 'success');
            }).catch(error => {
                console.error(error);
                this.showToast('Nie udało się utworzyć strefy.', 'danger');
            });
        };

        const createRackAtPosition = (zoneId, clientPosition = null) => {
            if (!zoneId) {
                return;
            }
            const zoneGroup = this.getZoneGroupById(zoneId);
            if (!zoneGroup) {
                return;
            }
            const metrics = this.calculateRackCreationMetrics(zoneGroup, clientPosition);
            if (!metrics) {
                return;
            }
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCsrfToken());
            formData.append('x', this.formatNumber(metrics.x));
            formData.append('y', this.formatNumber(metrics.y));
            formData.append('width', this.formatNumber(metrics.width));
            formData.append('height', this.formatNumber(metrics.height));
            formData.append('color', metrics.color);
            if (metrics.name) {
                formData.append('name', metrics.name);
            }
            fetch(`/wms-builder/zones/${zoneId}/racks/quick-create/`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Nie udało się utworzyć regału.');
                }
                return response.json();
            }).then(data => {
                if (!data || !data.rack) {
                    return;
                }
                const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
                if (!zoneMetrics) {
                    return;
                }
                const rackGroup = this.createRackElement(data.rack, zoneMetrics);
                if (!rackGroup) {
                    return;
                }
                zoneGroup.appendChild(rackGroup);
                this.bindRackSelectionHandlers(rackGroup);
                rackGroup.querySelectorAll('.draggable-shelf').forEach(shelf => {
                    this.bindShelfSelectionHandlers(shelf);
                });
                this.applyRackWorkspaceTransformIfNeeded(rackGroup);
                this.setSelection(rackGroup, 'rack');
                if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                    this.zoneMode.updateZonesVisibility();
                }
                const label = this.getEntityAccusativeLabel('rack');
                this.showToast(`Dodano ${label || 'regał'} "${data.rack.name}".`, 'success');
            }).catch(error => {
                console.error(error);
                this.showToast('Nie udało się utworzyć regału.', 'danger');
            });
        };

        const createShelfAtPosition = (rackId, clientPosition = null) => {
            if (!rackId) {
                return;
            }
            const rackGroup = this.getRackGroupById(rackId);
            if (!rackGroup) {
                return;
            }
            const metrics = this.calculateShelfCreationMetrics(rackGroup, clientPosition);
            if (!metrics) {
                return;
            }
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCsrfToken());
            formData.append('x', this.formatNumber(metrics.x));
            formData.append('y', this.formatNumber(metrics.y));
            formData.append('width', this.formatNumber(metrics.width));
            formData.append('height', this.formatNumber(metrics.height));
            formData.append('color', metrics.color);
            if (metrics.name) {
                formData.append('name', metrics.name);
            }
            fetch(`/wms-builder/racks/${rackId}/shelves/quick-create/`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Nie udało się utworzyć półki.');
                }
                return response.json();
            }).then(data => {
                if (!data || !data.shelf) {
                    return;
                }
                const zoneGroup = rackGroup.closest('.draggable-zone');
                const zoneMetrics = this.getZoneActualMetrics(zoneGroup);
                const rackMetrics = this.getRackActualMetrics(rackGroup);
                if (!zoneMetrics || !rackMetrics) {
                    return;
                }
                const shelfGroup = this.createShelfElement(data.shelf, {
                    zoneX: zoneMetrics.x,
                    zoneY: zoneMetrics.y,
                    rackX: rackMetrics.x,
                    rackY: rackMetrics.y
                });
                if (!shelfGroup) {
                    return;
                }
                rackGroup.appendChild(shelfGroup);
                this.bindShelfSelectionHandlers(shelfGroup);
                this.applyShelfWorkspaceTransformIfNeeded(shelfGroup);
                this.setSelection(shelfGroup, 'shelf');
                const label = this.getEntityAccusativeLabel('shelf');
                this.showToast(`Dodano ${label || 'półkę'} "${data.shelf.name}".`, 'success');
            }).catch(error => {
                console.error(error);
                this.showToast('Nie udało się utworzyć półki.', 'danger');
            });
        };
        
        // Context menu for zones, racks, and shelves
        this.svg.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            
            let target = e.target;
            const pointerPosition = { clientX: e.clientX, clientY: e.clientY };
            
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
                        action: () => createRackAtPosition(zoneId, pointerPosition)
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
                                    body: formData,
                                    headers: {
                                        'X-CSRFToken': this.getCsrfToken()
                                    }
                                }).then(response => {
                                    if (response.status === 204) {
                                        // Usuń strefę z DOM
                                        if (zoneGroup) {
                                            zoneGroup.remove();
                                        }
                                        // Sprawdź czy jesteśmy w tej strefie - jeśli tak, przejdź do widoku magazynu
                                        if (this.zoneMode.activeZoneId === zoneId) {
                                            this.setZoneMode(null);
                                        }
                                        // Usuń opcję z selecta jeśli istnieje
                                        if (this.zoneModeSelect) {
                                            const option = this.zoneModeSelect.querySelector(`option[value="${zoneId}"]`);
                                            if (option) {
                                                option.remove();
                                            }
                                        }
                                        // Wyczyść selekcję
                                        this.clearSelection();
                                        // Odśwież widoczność stref
                                        if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                                            this.zoneMode.updateZonesVisibility();
                                        }
                                        // Odczytaj HX-Trigger header i wywołaj eventy
                                        const triggerHeader = response.headers.get('HX-Trigger');
                                        if (triggerHeader && typeof htmx !== 'undefined') {
                                            try {
                                                const triggers = JSON.parse(triggerHeader);
                                                if (triggers.toastMessage) {
                                                    htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                                                }
                                                if (triggers.toastMessageList) {
                                                    htmx.trigger(document.body, 'toastMessageList', triggers.toastMessageList);
                                                }
                                            } catch (e) {
                                                console.error('Error parsing HX-Trigger:', e);
                                            }
                                        }
                                    }
                                }).catch(error => {
                                    console.error('Error deleting zone:', error);
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
                        action: () => createShelfAtPosition(rackId, pointerPosition)
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
                                    body: formData,
                                    headers: {
                                        'X-CSRFToken': this.getCsrfToken()
                                    }
                                }).then(response => {
                                    if (response.status === 204) {
                                        // Usuń regał z DOM
                                        if (rackGroup) {
                                            rackGroup.remove();
                                        }
                                        // Sprawdź czy jesteśmy w tym regale - jeśli tak, przekieruj do widoku strefy z toastem
                                        const isInRackDetailView = this.rackMode.activeRackId === rackId;
                                        const zoneIdForRedirect = rackGroup ? rackGroup.closest('.draggable-zone')?.getAttribute('data-zone-id') : null;
                                        
                                        if (isInRackDetailView && zoneIdForRedirect) {
                                            // Jeśli jesteśmy w widoku szczegółowym tego regału, przekieruj do widoku strefy
                                            if (typeof htmx !== 'undefined') {
                                                htmx.trigger(document.body, 'toastMessage', {
                                                    value: 'Regał został usunięty. Zostałeś przekierowany do widoku strefy.',
                                                    type: 'info'
                                                });
                                                sessionStorage.setItem('deleteToast', JSON.stringify({
                                                    value: 'Regał został usunięty. Zostałeś przekierowany do widoku strefy.',
                                                    type: 'info'
                                                }));
                                            }
                                            // Przekieruj do widoku strefy
                                            window.location.href = `/wms-builder/warehouses/${this.warehouseId}/zones/${zoneIdForRedirect}/?not_found=rack`;
                                            return;
                                        }
                                        
                                        if (this.rackMode.activeRackId === rackId) {
                                            this.setRackMode(null);
                                        }
                                        // Wyczyść selekcję
                                        this.clearSelection();
                                        // Odśwież widoczność stref/regalów
                                        if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                                            this.zoneMode.updateZonesVisibility();
                                        }
                                        // Odczytaj HX-Trigger header i wywołaj eventy
                                        const triggerHeader = response.headers.get('HX-Trigger');
                                        if (triggerHeader && typeof htmx !== 'undefined') {
                                            try {
                                                const triggers = JSON.parse(triggerHeader);
                                                if (triggers.toastMessage) {
                                                    htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                                                }
                                                if (triggers.toastMessageList) {
                                                    htmx.trigger(document.body, 'toastMessageList', triggers.toastMessageList);
                                                }
                                            } catch (e) {
                                                console.error('Error parsing HX-Trigger:', e);
                                            }
                                        }
                                    }
                                }).catch(error => {
                                    console.error('Error deleting rack:', error);
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
                                    body: formData,
                                    headers: {
                                        'X-CSRFToken': this.getCsrfToken()
                                    }
                                }).then(response => {
                                    // Odczytaj HX-Trigger header i wywołaj eventy (dla wszystkich statusów)
                                    const triggerHeader = response.headers.get('HX-Trigger');
                                    console.log('Shelf delete response status:', response.status);
                                    console.log('HX-Trigger header:', triggerHeader);
                                    
                                    if (triggerHeader && typeof htmx !== 'undefined') {
                                        try {
                                            const triggers = JSON.parse(triggerHeader);
                                            if (triggers.toastMessage) {
                                                htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                                            }
                                            if (triggers.toastMessageList) {
                                                htmx.trigger(document.body, 'toastMessageList', triggers.toastMessageList);
                                            }
                                        } catch (e) {
                                            console.error('Error parsing HX-Trigger:', e);
                                        }
                                    }
                                    
                                    if (response.status === 204) {
                                        // Usuń półkę z DOM
                                        if (shelfGroup) {
                                            shelfGroup.remove();
                                        }
                                        
                                        // Sprawdź czy jesteśmy w widoku regału, który zawiera tę półkę
                                        const rackGroupForShelf = shelfGroup ? shelfGroup.closest('.draggable-rack') : null;
                                        const rackIdForShelf = rackGroupForShelf ? rackGroupForShelf.getAttribute('data-rack-id') : null;
                                        const isInRackDetailView = rackIdForShelf && this.rackMode.activeRackId === rackIdForShelf;
                                        const zoneIdForShelf = rackGroupForShelf ? rackGroupForShelf.closest('.draggable-zone')?.getAttribute('data-zone-id') : null;
                                        
                                        if (isInRackDetailView && zoneIdForShelf && rackIdForShelf) {
                                            // Jeśli jesteśmy w widoku szczegółowym regału, który zawiera tę półkę,
                                            // przekieruj do widoku regału z toastem
                                            if (typeof htmx !== 'undefined') {
                                                htmx.trigger(document.body, 'toastMessage', {
                                                    value: 'Półka została usunięta. Zostałeś przekierowany do widoku regału.',
                                                    type: 'info'
                                                });
                                                sessionStorage.setItem('deleteToast', JSON.stringify({
                                                    value: 'Półka została usunięta. Zostałeś przekierowany do widoku regału.',
                                                    type: 'info'
                                                }));
                                            }
                                            // Przekieruj do widoku regału
                                            window.location.href = `/wms-builder/warehouses/${this.warehouseId}/zones/${zoneIdForShelf}/racks/${rackIdForShelf}/?not_found=shelf`;
                                            return;
                                        }
                                        
                                        // Wyczyść selekcję
                                        this.clearSelection();
                                    } else if (response.status === 400 || response.status === 200) {
                                        // Status 400/200 - błąd walidacji, toast message już został wyświetlony przez HX-Trigger powyżej
                                        // Nie usuwaj półki z DOM i nie przekierowuj
                                        return;
                                    }
                                }).catch(error => {
                                    console.error('Error deleting shelf:', error);
                                    // Wyświetl ogólny komunikat błędu
                                    if (typeof htmx !== 'undefined') {
                                        htmx.trigger(document.body, 'toastMessage', {
                                            value: 'Nie udało się usunąć półki.',
                                            type: 'danger'
                                        });
                                    }
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
                        action: () => createShelfAtPosition(activeRackId, pointerPosition)
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
                            action: () => createRackAtPosition(zoneId, pointerPosition)
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
                                        body: formData,
                                        headers: {
                                            'X-CSRFToken': this.getCsrfToken()
                                        }
                                    }).then(response => {
                                        if (response.status === 204) {
                                            // Usuń strefę z DOM
                                            if (focusedZone) {
                                                focusedZone.remove();
                                            }
                                            // Usuń opcję z selecta jeśli istnieje
                                            if (this.zoneModeSelect) {
                                                const option = this.zoneModeSelect.querySelector(`option[value="${zoneId}"]`);
                                                if (option) {
                                                    option.remove();
                                                }
                                            }
                                            // Wyczyść selekcję
                                            this.clearSelection();
                                            // Przejdź do widoku magazynu
                                            this.navigateToZone(null);
                                            // Odśwież widoczność stref
                                            if (typeof this.zoneMode.updateZonesVisibility === 'function') {
                                                this.zoneMode.updateZonesVisibility();
                                            }
                                            // Odczytaj HX-Trigger header i wywołaj eventy
                                            const triggerHeader = response.headers.get('HX-Trigger');
                                            if (triggerHeader && typeof htmx !== 'undefined') {
                                                try {
                                                    const triggers = JSON.parse(triggerHeader);
                                                    if (triggers.toastMessage) {
                                                        htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                                                    }
                                                    if (triggers.toastMessageList) {
                                                        htmx.trigger(document.body, 'toastMessageList', triggers.toastMessageList);
                                                    }
                                                } catch (e) {
                                                    console.error('Error parsing HX-Trigger:', e);
                                                }
                                            }
                                        }
                                    }).catch(error => {
                                        console.error('Error deleting zone:', error);
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
                    action: () => createZoneAtPosition(pointerPosition)
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
            if (!normalized) {
                this.applyZoneBackground(null);
            }
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
            this.applyZoneBackground(zoneGroup);
            if (!this.rackMode.activeRackId) {
                this.setRackMode(null, { updateVisibility: false });
            }
        } else {
            this.applyZoneBackground(null);
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
        const workspaceMaxWidth = this.zoneMode.workspaceWidth || zoneWidth;
        const workspaceMaxHeight = this.zoneMode.workspaceHeight || zoneHeight;
        let workspaceWidth = workspaceMaxWidth;
        let workspaceHeight = workspaceMaxHeight;
        if (workspaceMaxWidth && workspaceMaxHeight && zoneWidth && zoneHeight) {
            const zoneAspect = zoneWidth / zoneHeight;
            const workspaceAspect = workspaceMaxWidth / workspaceMaxHeight;
            if (workspaceAspect > zoneAspect) {
                workspaceWidth = workspaceMaxHeight * zoneAspect;
                workspaceHeight = workspaceMaxHeight;
            } else {
                workspaceWidth = workspaceMaxWidth;
                workspaceHeight = workspaceMaxWidth / zoneAspect;
            }
        }

        zoneGroup.dataset.zoneOriginalX = zoneX;
        zoneGroup.dataset.zoneOriginalY = zoneY;
        zoneGroup.dataset.zoneOriginalWidth = zoneWidth;
        zoneGroup.dataset.zoneOriginalHeight = zoneHeight;
        const zoneRectOriginal = zoneGroup.querySelector('.zone-rect');
        if (zoneRectOriginal && !zoneGroup.dataset.zoneOriginalFill) {
            const originalFill = zoneRectOriginal.getAttribute('fill') || this.defaultBackground;
            const originalOpacity = zoneRectOriginal.getAttribute('fill-opacity') || '0.3';
            zoneGroup.dataset.zoneOriginalFill = originalFill;
            zoneGroup.dataset.zoneOriginalFillOpacity = originalOpacity;
        }
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
            if (zoneGroup.dataset.zoneOriginalFill) {
                zoneRect.setAttribute('fill', zoneGroup.dataset.zoneOriginalFill);
            }
            if (zoneGroup.dataset.zoneOriginalFillOpacity) {
                zoneRect.setAttribute('fill-opacity', zoneGroup.dataset.zoneOriginalFillOpacity);
            }
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
            if (zoneGroup.dataset.zoneOriginalFill) {
                zoneRect.setAttribute('fill', zoneGroup.dataset.zoneOriginalFill);
            }
            if (zoneGroup.dataset.zoneOriginalFillOpacity) {
                zoneRect.setAttribute('fill-opacity', zoneGroup.dataset.zoneOriginalFillOpacity);
            }
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
        const rackZoneMetrics = this.convertRackMetricsForServer(rackGroup, { x: rackX, y: rackY, width: rackWidth, height: rackHeight }) || {};
        const originalZoneX = typeof rackZoneMetrics.x === 'number' ? rackZoneMetrics.x : rackX;
        const originalZoneY = typeof rackZoneMetrics.y === 'number' ? rackZoneMetrics.y : rackY;
        const originalZoneWidth = typeof rackZoneMetrics.width === 'number' ? rackZoneMetrics.width : rackWidth;
        const originalZoneHeight = typeof rackZoneMetrics.height === 'number' ? rackZoneMetrics.height : rackHeight;
        const workspaceMaxWidth = this.zoneMode.workspaceWidth || rackWidth;
        const workspaceMaxHeight = this.zoneMode.workspaceHeight || rackHeight;
        let workspaceWidth = workspaceMaxWidth;
        let workspaceHeight = workspaceMaxHeight;
        if (workspaceMaxWidth && workspaceMaxHeight && rackWidth && rackHeight) {
            const rackAspect = rackWidth / rackHeight;
            const workspaceAspect = workspaceMaxWidth / workspaceMaxHeight;
            if (workspaceAspect > rackAspect) {
                workspaceWidth = workspaceMaxHeight * rackAspect;
                workspaceHeight = workspaceMaxHeight;
            } else {
                workspaceWidth = workspaceMaxWidth;
                workspaceHeight = workspaceMaxWidth / rackAspect;
            }
        }

        rackGroup.dataset.rackDetailOriginalX = rackX;
        rackGroup.dataset.rackDetailOriginalY = rackY;
        rackGroup.dataset.rackDetailOriginalWidth = rackWidth;
        rackGroup.dataset.rackDetailOriginalHeight = rackHeight;
        rackGroup.dataset.rackDetailZoneX = originalZoneX;
        rackGroup.dataset.rackDetailZoneY = originalZoneY;
        rackGroup.dataset.rackDetailZoneWidth = originalZoneWidth;
        rackGroup.dataset.rackDetailZoneHeight = originalZoneHeight;
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
        delete rackGroup.dataset.rackDetailZoneX;
        delete rackGroup.dataset.rackDetailZoneY;
        delete rackGroup.dataset.rackDetailZoneWidth;
        delete rackGroup.dataset.rackDetailZoneHeight;
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
        if (rack.dataset.zoneWorkspaceMode === '1') {
            return;
        }
        const originalX = parseFloat(rack.getAttribute('data-x')) || 0;
        const originalY = parseFloat(rack.getAttribute('data-y')) || 0;
        const originalWidth = parseFloat(rack.getAttribute('data-width')) || 0;
        const originalHeight = parseFloat(rack.getAttribute('data-height')) || 0;

        const workspaceX = zoneWidth ? (originalX / zoneWidth) * workspaceWidth : originalX;
        const workspaceY = zoneHeight ? (originalY / zoneHeight) * workspaceHeight : originalY;
        const workspaceRackWidth = zoneWidth ? (originalWidth / zoneWidth) * workspaceWidth : originalWidth;
        const workspaceRackHeight = zoneHeight ? (originalHeight / zoneHeight) * workspaceHeight : originalHeight;

        rack.dataset.zoneWorkspaceMode = '1';
        rack.dataset.zoneWorkspaceOriginalX = originalX;
        rack.dataset.zoneWorkspaceOriginalY = originalY;
        rack.dataset.zoneWorkspaceOriginalWidth = originalWidth;
        rack.dataset.zoneWorkspaceOriginalHeight = originalHeight;
        rack.dataset.zoneWorkspaceWidth = workspaceRackWidth;
        rack.dataset.zoneWorkspaceHeight = workspaceRackHeight;

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

        delete rack.dataset.zoneWorkspaceMode;
        delete rack.dataset.zoneWorkspaceOriginalX;
        delete rack.dataset.zoneWorkspaceOriginalY;
        delete rack.dataset.zoneWorkspaceOriginalWidth;
        delete rack.dataset.zoneWorkspaceOriginalHeight;
        delete rack.dataset.zoneWorkspaceWidth;
        delete rack.dataset.zoneWorkspaceHeight;
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

    applyZoneBackground(zoneGroup) {
        if (!this.svgContainer) {
            return;
        }
        if (!zoneGroup) {
            this.svgContainer.style.background = this.defaultBackground;
            if (this.svg) {
                this.svg.style.background = '';
            }
            return;
        }
        const zoneRect = zoneGroup.querySelector('.zone-rect');
        if (!zoneRect) {
            this.svgContainer.style.background = this.defaultBackground;
            if (this.svg) {
                this.svg.style.background = '';
            }
            return;
        }
        const zoneStyle = window.getComputedStyle(zoneRect);
        const fillColor = zoneRect.getAttribute('fill') || zoneStyle.fill || this.defaultBackground;
        const opacityAttr = zoneRect.dataset.originalFillOpacity || zoneRect.dataset.zoneOriginalFillOpacity || zoneRect.getAttribute('data-fill-opacity');
        const fillOpacity = opacityAttr !== undefined && opacityAttr !== null
            ? parseFloat(opacityAttr)
            : parseFloat(zoneRect.getAttribute('fill-opacity') || zoneStyle.fillOpacity || '0.3');
        const rgbaColor = this.getColorWithOpacity(fillColor, fillOpacity);
        const backgroundColor = rgbaColor || fillColor;
        this.svgContainer.style.background = backgroundColor;
        if (this.svg) {
            this.svg.style.background = '';
        }
    }

    getColorWithOpacity(color, alpha = 0.3) {
        if (!color) {
            return null;
        }
        const normalizedAlpha = Math.min(Math.max(alpha, 0), 1);
        if (color.startsWith('#')) {
            const hex = color.replace('#', '');
            if (hex.length === 3) {
                const r = parseInt(hex[0] + hex[0], 16);
                const g = parseInt(hex[1] + hex[1], 16);
                const b = parseInt(hex[2] + hex[2], 16);
                return `rgba(${r}, ${g}, ${b}, ${normalizedAlpha})`;
            }
            if (hex.length === 6) {
                const r = parseInt(hex.substring(0, 2), 16);
                const g = parseInt(hex.substring(2, 4), 16);
                const b = parseInt(hex.substring(4, 6), 16);
                return `rgba(${r}, ${g}, ${b}, ${normalizedAlpha})`;
            }
        } else if (color.startsWith('rgb')) {
            const match = color.match(/rgba?\(([^)]+)\)/);
            if (match && match[1]) {
                const [r, g, b] = match[1].split(',').map(v => v.trim());
                return `rgba(${r}, ${g}, ${b}, ${normalizedAlpha})`;
            }
        }
        return color;
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

        const detailZoneWidth = parseFloat(rack.dataset.rackDetailZoneWidth || rack.dataset.rackDetailOriginalWidth || '') || null;
        const detailZoneHeight = parseFloat(rack.dataset.rackDetailZoneHeight || rack.dataset.rackDetailOriginalHeight || '') || null;
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
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());
        
        fetch(`/wms-builder/zones/${zoneId}/sync-to-location/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            }
        }).then(response => {
            if (response.status === 204) {
                // Odczytaj HX-Trigger header i wywołaj eventy
                const triggerHeader = response.headers.get('HX-Trigger');
                if (triggerHeader && typeof htmx !== 'undefined') {
                    try {
                        const triggers = JSON.parse(triggerHeader);
                        if (triggers.toastMessage) {
                            // Wyświetl toast message przed odświeżeniem
                            htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                            // Zapisz toast w sessionStorage na wypadek odświeżenia
                            sessionStorage.setItem('syncToast', JSON.stringify(triggers.toastMessage));
                        }
                        if (triggers.modalHide) {
                            htmx.trigger(document.body, 'modalHide');
                        }
                    } catch (e) {
                        console.error('Error parsing HX-Trigger:', e);
                    }
                }
                // Odśwież stronę z opóźnieniem, aby toast zdążył się wyświetlić
                if (response.headers.get('HX-Refresh') === 'true') {
                    setTimeout(() => {
                        window.location.reload();
                    }, 500); // 500ms opóźnienia, aby toast był widoczny
                }
            } else {
                // Jeśli błąd, wyświetl toast z błędem
                if (typeof htmx !== 'undefined') {
                    htmx.trigger(document.body, 'toastMessage', {
                        value: 'Błąd podczas synchronizacji strefy',
                        type: 'danger'
                    });
                }
            }
        }).catch(error => {
            console.error('Error synchronizing zone:', error);
            if (typeof htmx !== 'undefined') {
                htmx.trigger(document.body, 'toastMessage', {
                    value: 'Błąd podczas synchronizacji strefy',
                    type: 'danger'
                });
            }
        });
    }

    syncRack(rackId) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());
        
        fetch(`/wms-builder/racks/${rackId}/sync-to-location/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            }
        }).then(response => {
            if (response.status === 204) {
                // Odczytaj HX-Trigger header i wywołaj eventy
                const triggerHeader = response.headers.get('HX-Trigger');
                if (triggerHeader && typeof htmx !== 'undefined') {
                    try {
                        const triggers = JSON.parse(triggerHeader);
                        if (triggers.toastMessage) {
                            // Wyświetl toast message przed odświeżeniem
                            htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                            // Zapisz toast w sessionStorage na wypadek odświeżenia
                            sessionStorage.setItem('syncToast', JSON.stringify(triggers.toastMessage));
                        }
                        if (triggers.modalHide) {
                            htmx.trigger(document.body, 'modalHide');
                        }
                    } catch (e) {
                        console.error('Error parsing HX-Trigger:', e);
                    }
                }
                // Odśwież stronę z opóźnieniem, aby toast zdążył się wyświetlić
                if (response.headers.get('HX-Refresh') === 'true') {
                    setTimeout(() => {
                        window.location.reload();
                    }, 500); // 500ms opóźnienia, aby toast był widoczny
                }
            } else {
                // Jeśli błąd, wyświetl toast z błędem
                if (typeof htmx !== 'undefined') {
                    htmx.trigger(document.body, 'toastMessage', {
                        value: 'Błąd podczas synchronizacji regału',
                        type: 'danger'
                    });
                }
            }
        }).catch(error => {
            console.error('Error synchronizing rack:', error);
            if (typeof htmx !== 'undefined') {
                htmx.trigger(document.body, 'toastMessage', {
                    value: 'Błąd podczas synchronizacji regału',
                    type: 'danger'
                });
            }
        });
    }

    syncShelf(shelfId) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());
        
        fetch(`/wms-builder/shelves/${shelfId}/sync-to-location/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            }
        }).then(response => {
            if (response.status === 204) {
                // Odczytaj HX-Trigger header i wywołaj eventy
                const triggerHeader = response.headers.get('HX-Trigger');
                if (triggerHeader && typeof htmx !== 'undefined') {
                    try {
                        const triggers = JSON.parse(triggerHeader);
                        if (triggers.toastMessage) {
                            // Wyświetl toast message przed odświeżeniem
                            htmx.trigger(document.body, 'toastMessage', triggers.toastMessage);
                            // Zapisz toast w sessionStorage na wypadek odświeżenia
                            sessionStorage.setItem('syncToast', JSON.stringify(triggers.toastMessage));
                        }
                        if (triggers.modalHide) {
                            htmx.trigger(document.body, 'modalHide');
                        }
                    } catch (e) {
                        console.error('Error parsing HX-Trigger:', e);
                    }
                }
                // Odśwież stronę z opóźnieniem, aby toast zdążył się wyświetlić
                if (response.headers.get('HX-Refresh') === 'true') {
                    setTimeout(() => {
                        window.location.reload();
                    }, 500); // 500ms opóźnienia, aby toast był widoczny
                }
            } else {
                // Jeśli błąd, wyświetl toast z błędem
                if (typeof htmx !== 'undefined') {
                    htmx.trigger(document.body, 'toastMessage', {
                        value: 'Błąd podczas synchronizacji półki',
                        type: 'danger'
                    });
                }
            }
        }).catch(error => {
            console.error('Error synchronizing shelf:', error);
            if (typeof htmx !== 'undefined') {
                htmx.trigger(document.body, 'toastMessage', {
                    value: 'Błąd podczas synchronizacji półki',
                    type: 'danger'
                });
            }
        });
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

    showToast(message, type = 'success') {
        if (!message) {
            return;
        }
        if (typeof htmx !== 'undefined' && typeof htmx.trigger === 'function') {
            htmx.trigger(document.body, 'toastMessage', {
                value: message,
                type
            });
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
}

