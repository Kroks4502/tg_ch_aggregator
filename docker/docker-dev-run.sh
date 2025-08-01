#!/bin/bash

# Script for managing Docker containers of tg_ch_aggregator

set -e

cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
}

stop() {
    print_info "Stopping tg_ch_aggregator..."
    docker-compose -f docker-compose.dev.yml --env-file ../.env down
    print_info "Services stopped!"
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
}

logs() {
    if [ -z "$1" ]; then
        docker-compose -f docker-compose.dev.yml --env-file ../.env logs -f
    else
        docker-compose -f docker-compose.dev.yml --env-file ../.env logs -f "$1"
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
    echo -n "Continue? [y/N] "
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
    echo "  status          - Show status of services"
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
    status)
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
