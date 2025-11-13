/**
 * Warehouse Builder - Drag and Drop functionality
 */

class WarehouseBuilder {
    constructor(warehouseData) {
        this.warehouseData = warehouseData;
        this.svg = null;
        this.currentZoom = 1;
        this.draggedElement = null;
    }

    init() {
        console.log('WarehouseBuilder.init() called');
        this.svg = document.getElementById('warehouse-svg');
        if (!this.svg) {
            console.error('SVG element not found!');
            return;
        }
        console.log('SVG element found:', this.svg);

        this.setupDragAndDrop();
        this.setupClickToEdit();
        this.setupContextMenu();
        this.setupZoomControls();
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
                    
                    // Update child racks
                    const racks = target.querySelectorAll('.draggable-rack');
                    racks.forEach(rack => {
                        const rackX = parseFloat(rack.getAttribute('data-x')) || 0;
                        const rackY = parseFloat(rack.getAttribute('data-y')) || 0;
                        const rackRect = rack.querySelector('.rack-rect');
                        if (rackRect) {
                            rackRect.setAttribute('x', x + rackX);
                            rackRect.setAttribute('y', y + rackY);
                        }
                        const rackText = rack.querySelector('text');
                        if (rackText) {
                            rackText.setAttribute('x', x + rackX + 40);
                            rackText.setAttribute('y', y + rackY + 30);
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
                    
                    const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
                    
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);
                    
                    const rect = target.querySelector('.rack-rect');
                    const width = parseFloat(target.getAttribute('data-width')) || 80;
                    const height = parseFloat(target.getAttribute('data-height')) || 60;
                    
                    if (rect) {
                        rect.setAttribute('x', zoneX + x);
                        rect.setAttribute('y', zoneY + y);
                    }
                    
                    const text = target.querySelector('text');
                    if (text) {
                        text.setAttribute('x', zoneX + x + width / 2);
                        text.setAttribute('y', zoneY + y + height / 2);
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
                    
                    this.updateRackPosition(rackId, x, y);
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
                
                this.updateRackSize(rackId, width, height);
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
                    
                    const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
                    
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);
                    
                    const rect = target.querySelector('.shelf-rect');
                    const width = parseFloat(target.getAttribute('data-width')) || 60;
                    const height = parseFloat(target.getAttribute('data-height')) || 20;
                    
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
                    
                    this.updateShelfPosition(shelfId, x, y);
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
                
                this.updateShelfSize(shelfId, width, height);
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
                        // Double click - edit
                        clearTimeout(clickTimer);
                        clickTimer = null;
                        e.stopPropagation();
                        const zoneId = zoneGroup.getAttribute('data-zone-id');
                        if (zoneId) {
                            this.editZone(zoneId);
                        }
                    }
                    
                    mouseDownPos = { x: 0, y: 0 };
                });
            });

            // Handle racks - single click selects, double click edits
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
                        // Double click - edit
                        clearTimeout(clickTimer);
                        clickTimer = null;
                        e.stopPropagation();
                        const rackId = rackGroup.getAttribute('data-rack-id');
                        if (rackId) {
                            this.editRack(rackId);
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
            }
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

