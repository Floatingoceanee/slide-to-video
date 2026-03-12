#!/bin/bash
# TTS 模型管理脚本

MODEL_DIR="${TTS_HOME:-$HOME/models/tts}"

mkdir -p "$MODEL_DIR"

list_models() {
    echo "已下载的 TTS 模型:"
    echo "-------------------"
    if [ -d "$MODEL_DIR" ]; then
        find "$MODEL_DIR" -type d -maxdepth 2 | grep -v "^$MODEL_DIR$" | sed "s|$MODEL_DIR/||"
    else
        echo "(无)"
    fi
}

disk_usage() {
    echo "模型目录磁盘占用:"
    du -sh "$MODEL_DIR" 2>/dev/null || echo "目录不存在"
}

clean_cache() {
    echo "清理未完成的下载缓存..."
    find "$MODEL_DIR" -type d -name "*.tmp" -exec rm -rf {} + 2>/dev/null
    echo "完成"
}

backup_models() {
    local backup_path="$1"
    if [ -z "$backup_path" ]; then
        echo "用法: $0 backup <目标路径>"
        exit 1
    fi
    echo "备份模型到 $backup_path ..."
    rsync -av --progress "$MODEL_DIR/" "$backup_path/"
}

case "$1" in
    list)   list_models ;;
    size)   disk_usage ;;
    clean)  clean_cache ;;
    backup) backup_models "$2" ;;
    *)
        echo "用法: $0 {list|size|clean|backup <path>}"
        echo ""
        echo "  list   - 列出已下载的模型"
        echo "  size   - 查看磁盘占用"
        echo "  clean  - 清理临时文件"
        echo "  backup - 备份模型到指定目录"
        ;;
esac
