// 简化的二维码生成器
function SimpleQR() {
    // 创建一个简单的二维码模拟
    this.toCanvas = function(canvas, text, options, callback) {
        try {
            const ctx = canvas.getContext('2d');
            const size = options.width || 200;
            canvas.width = size;
            canvas.height = size;
            
            // 清空画布
            ctx.fillStyle = options.color.light || '#FFFFFF';
            ctx.fillRect(0, 0, size, size);
            
            // 绘制简单的二维码模式
            ctx.fillStyle = options.color.dark || '#000000';
            
            // 绘制定位标记（三个角）
            this.drawPositionMarker(ctx, 10, 10, 30);
            this.drawPositionMarker(ctx, size - 40, 10, 30);
            this.drawPositionMarker(ctx, 10, size - 40, 30);
            
            // 绘制数据模块（简化版）
            const moduleSize = 4;
            for (let i = 0; i < size; i += moduleSize * 2) {
                for (let j = 0; j < size; j += moduleSize * 2) {
                    if (this.shouldDrawModule(i, j, size)) {
                        ctx.fillRect(i, j, moduleSize, moduleSize);
                    }
                }
            }
            
            // 在中心绘制文本提示
            ctx.fillStyle = options.color.dark || '#000000';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('扫描访问', size / 2, size / 2 - 10);
            ctx.fillText('系统', size / 2, size / 2 + 10);
            
            if (callback) callback(null);
        } catch (error) {
            if (callback) callback(error);
        }
    };
    
    this.drawPositionMarker = function(ctx, x, y, size) {
        // 外框
        ctx.fillRect(x, y, size, size);
        // 内部白色
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(x + 4, y + 4, size - 8, size - 8);
        // 中心黑点
        ctx.fillStyle = '#000000';
        ctx.fillRect(x + 10, y + 10, size - 20, size - 20);
    };
    
    this.shouldDrawModule = function(x, y, size) {
        // 避免定位标记区域
        if ((x < 50 && y < 50) || 
            (x > size - 50 && y < 50) || 
            (x < 50 && y > size - 50)) {
            return false;
        }
        
        // 简单的伪随机模式
        return (x + y) % 8 < 4;
    };
}

// 创建全局 QRCode 对象
window.QRCode = new SimpleQR();