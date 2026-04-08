#!/bin/bash

# Git 快捷工具 - 中文界面
# 路径: git-tool.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取当前目录名
CURRENT_DIR=$(basename "$(pwd)")

show_menu() {
    clear
    echo -e "${BLUE}=======================================${NC}"
    echo -e "${BLUE}      Git 快捷工具 - 中文界面${NC}"
    echo -e "${BLUE}=======================================${NC}"
    echo ""
    echo -e "当前目录: ${YELLOW}$(pwd)${NC}"
    echo ""
    echo -e "${GREEN}1${NC}. 初始化仓库 (git init)"
    echo -e "${GREEN}2${NC}. 查看状态 (git status)"
    echo -e "${GREEN}3${NC}. 添加并提交 (git add + commit)"
    echo -e "${GREEN}4${NC}. 查看日志 (git log)"
    echo -e "${GREEN}5${NC}. 上传代码 (git push)"
    echo -e "${GREEN}6${NC}. 下载代码 (git pull)"
    echo -e "${GREEN}7${NC}. 查看差异 (git diff)"
    echo -e "${GREEN}8${NC}. 查看分支 (git branch)"
    echo -e "${GREEN}9${NC}. 切换分支 (git checkout)"
    echo -e "${GREEN}10${NC}. 合并分支 (git merge)"
    echo -e "${GREEN}0${NC}. 退出"
    echo ""
    echo -e "${BLUE}=======================================${NC}"
    echo -n "请输入选项 [0-10]: "
}

init_repo() {
    echo -e "${YELLOW}正在初始化 Git 仓库...${NC}"
    git init -b main
    echo -e "${GREEN}✓ 仓库初始化完成！${NC}"
}

show_status() {
    echo -e "${YELLOW}正在查看状态...${NC}"
    git status
}

commit_changes() {
    echo -n "请输入提交信息: "
    read -r msg
    if [ -z "$msg" ]; then
        msg="更新于 $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    echo -e "${YELLOW}正在添加文件并提交...${NC}"
    git add -A
    git commit -m "$msg"
    echo -e "${GREEN}✓ 提交完成！${NC}"
}

show_log() {
    echo -e "${YELLOW}最近10条提交记录:${NC}"
    git log -10 --graph --pretty=format:'%h -%d %s (%cr) <%an>' --abbrev-commit
}

push_code() {
    echo -e "${YELLOW}正在上传代码...${NC}"
    git push
    echo -e "${GREEN}✓ 上传完成！${NC}"
}

pull_code() {
    echo -e "${YELLOW}正在下载代码...${NC}"
    git pull --no-rebase
    echo -e "${GREEN}✓ 下载完成！${NC}"
}

show_diff() {
    echo -e "${YELLOW}查看文件差异:${NC}"
    git diff
}

show_branch() {
    echo -e "${YELLOW}当前分支:${NC}"
    git branch -a
}

switch_branch() {
    echo -n "请输入分支名: "
    read -r branch
    if [ -z "$branch" ]; then
        echo -e "${RED}分支名不能为空！${NC}"
        return
    fi
    echo -e "${YELLOW}正在切换到分支: $branch${NC}"
    git checkout "$branch"
    echo -e "${GREEN}✓ 切换完成！${NC}"
}

merge_branch() {
    echo -n "请输入要合并的分支名: "
    read -r branch
    if [ -z "$branch" ]; then
        echo -e "${RED}分支名不能为空！${NC}"
        return
    fi
    echo -e "${YELLOW}正在合并分支: $branch${NC}"
    git merge "$branch"
    echo -e "${GREEN}✓ 合并完成！${NC}"
}

# 检查是否为 Git 仓库
check_git_repo() {
    if [ ! -d ".git" ]; then
        return 1
    fi
    return 0
}

# 主循环
while true; do
    show_menu
    read -r choice

    case $choice in
        1)
            init_repo
            ;;
        2)
            show_status
            ;;
        3)
            commit_changes
            ;;
        4)
            show_log
            ;;
        5)
            push_code
            ;;
        6)
            pull_code
            ;;
        7)
            show_diff
            ;;
        8)
            show_branch
            ;;
        9)
            switch_branch
            ;;
        10)
            merge_branch
            ;;
        0)
            echo -e "${BLUE}感谢使用 Git 快捷工具！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请重新输入！${NC}"
            ;;
    esac

    echo ""
    echo -n "按 Enter 键继续..."
    read -r
done
