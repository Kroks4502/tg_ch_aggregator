#!/bin/bash

# Script for managing Docker containers of tg_ch_aggregator

set -e

cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_question() {
    echo -e "${BLUE}[?]${NC} $1"
}

check_env_file() {
    if [ ! -f "../.env" ]; then
        print_error "File .env not found in the root directory of the project!"
        print_info "Create a .env file based on .env.example"
        print_info "Example content of .env:"
        echo ""
        if [ -f "../.env.template" ]; then
            cat "../.env.template"
        else
            echo "# Create a .env file with your settings"
        fi
        echo ""
        exit 1
    fi
}

start() {
    print_info "Starting tg_ch_aggregator in Docker..."
    check_env_file
    docker-compose -f docker-compose.dev.yml --env-file ../.env up -d
    print_info "Services started!"
    print_info "For viewing logs, use: $0 logs"
    suggest_logs "$1"
}

stop() {
    print_info "Stopping tg_ch_aggregator..."
    docker-compose -f docker-compose.dev.yml --env-file ../.env down
    print_info "Services stopped!"
    suggest_logs "$1"
}

restart() {
    if [ -z "$1" ]; then
        print_info "Restarting all tg_ch_aggregator services..."
        docker-compose -f docker-compose.dev.yml --env-file ../.env down
        docker-compose -f docker-compose.dev.yml --env-file ../.env up -d
        print_info "All services restarted!"
    else
        print_info "Restarting service: $1"
        docker-compose -f docker-compose.dev.yml --env-file ../.env restart "$1"
        print_info "Service $1 restarted!"
    fi
    suggest_logs "$1"
}

suggest_logs() {
    print_question "Do you want to see logs after restart? [y/N]"
    read -r answer
    if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
        logs "$1"
        exit 0
    fi
}

logs() {
    if [ -z "$1" ]; then
        cids=$(docker-compose -f docker-compose.dev.yml --env-file ../.env ps -q)
        if [ -z "$cids" ]; then
            print_error "No containers running!"
            exit 1
        fi
        early_started=$(docker inspect -f '{{.State.StartedAt}}' $cids | sort | head -n1)
        print_info "Logs for all services (since $early_started)"
        docker-compose -f docker-compose.dev.yml --env-file ../.env logs --since "$early_started" -f
    else
        if ! docker-compose -f docker-compose.dev.yml --env-file ../.env ps "$1" >/dev/null 2>&1; then
            print_error "Service '$1' not found!"
            print_info "Available services:"
            docker-compose -f docker-compose.dev.yml --env-file ../.env ps --services
            exit 1
        fi
        cid=$(docker-compose -f docker-compose.dev.yml --env-file ../.env ps -q "$1")
        if [ -z "$cid" ]; then
            print_error "Service '$1' is not running!"
            exit 1
        fi
        started=$(docker inspect -f '{{.State.StartedAt}}' "$cid")
        print_info "Logs for service '$1' (container: $cid, since $started)"
        docker-compose -f docker-compose.dev.yml --env-file ../.env logs --since "$started" -f "$1"
    fi
}

create_sessions() {
    print_info "Creating Telegram sessions..."
    check_env_file
    docker-compose -f docker-compose.dev.yml --env-file ../.env run --rm create_sessions
}

build() {
    print_info "Building Docker images..."
    docker-compose -f docker-compose.dev.yml --env-file ../.env build
}

clean() {
    print_warning "All containers, images, and volumes will be cleaned."
    print_question "Continue? [y/N]"
    read -r answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        print_info "Operation cancelled"
        exit 1
    fi
    docker-compose -f docker-compose.dev.yml --env-file ../.env down --rmi all --volumes --remove-orphans
    print_info "Cleaning completed!"
}

status() {
    print_info "Status of services:"
    docker-compose -f docker-compose.dev.yml --env-file ../.env ps
}

help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start           - Start services"
    echo "  stop            - Stop services"
    echo "  restart [service] - Restart services (optional specify service)"
    echo "  logs [service]  - Show logs (optional specify service)"
    echo "  create_sessions - Create Telegram sessions"
    echo "  build           - Build Docker images"
    echo "  clean           - Clean containers and images"
    echo "  ps              - Show status of services"
    echo "  help            - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 restart"
    echo "  $0 restart backend"
    echo "  $0 restart postgres"
    echo "  $0 logs backend"
    echo "  $0 create_sessions"
}

case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart "$2"
        ;;
    logs)
        logs "$2"
        ;;
    create_sessions)
        create_sessions
        ;;
    build)
        build
        ;;
    clean)
        clean
        ;;
    ps)
        status
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        help
        exit 1
        ;;
esac
