#!/bin/bash
# ============================================
# Git 一键推送脚本
# ============================================

# ====== 配置区域 ======
COMMIT_MSG="${1:-更新代码: $(date '+%Y-%m-%d %H:%M')}"  # 提交信息，默认带时间戳
REMOTE_NAME="origin"                                      # 远程仓库名称
BRANCH_NAME="main"                                        # 分支名称

# ====== 颜色定义 ======
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # 重置颜色

# ====== 打印函数 ======
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Git 一键推送${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}>>> ${NC}$1"
}

print_error() {
    echo -e "${RED}!!! 错误: ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}??? 警告: ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ 成功: ${NC}$1"
}

# ====== 主流程 ======
main() {
    print_header

    # --- 步骤1: 检查 Git 状态 ---
    print_step "检查 Git 仓库..."
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "当前目录不是 Git 仓库"
        exit 1
    fi
    print_success "Git 仓库正常"

    # --- 步骤2: 检查远程仓库 ---
    print_step "检查远程仓库..."
    REMOTE_URL=$(git remote get-url "$REMOTE_NAME" 2>/dev/null)
    if [ -z "$REMOTE_URL" ]; then
        print_error "未找到远程仓库 '$REMOTE_NAME'"
        echo "请先添加远程仓库: git remote add $REMOTE_NAME <仓库地址>"
        exit 1
    fi
    print_success "远程仓库: $REMOTE_URL"

    # --- 步骤3: 添加文件到暂存区 ---
    print_step "添加文件到暂存区..."
    git add .
    print_success "文件已添加"

    # --- 步骤4: 检查是否有变更 ---
    print_step "检查变更..."
    if git diff --cached --quiet; then
        print_warning "没有检测到变更，无需提交"
        exit 0
    fi

    # --- 步骤5: 显示变更统计 ---
    echo ""
    echo "变更文件:"
    git status --short
    echo ""

    # --- 步骤6: 提交代码 ---
    print_step "提交代码..."
    echo "提交信息: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
    print_success "提交完成"

    # --- 步骤7: 推送到远程 ---
    print_step "推送到远程仓库..."
    echo "远程: $REMOTE_NAME"
    echo "分支: $BRANCH_NAME"
    echo ""

    if git push "$REMOTE_NAME" "$BRANCH_NAME"; then
        print_success "推送成功!"
    else
        print_error "推送失败!"
        echo "提示: 检查网络连接或 GitHub 认证状态"
        exit 1
    fi

    # --- 完成 ---
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  全部完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# ====== 执行主函数 ======
main
