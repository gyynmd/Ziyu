#!/system/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Read backend records as data. Each load opens one committed file once.
# Fixed keys only; preserve the first value, literal text and CRLF compatibility.
_ZIYU_BACKEND_CR="$(printf '\r')"

ziyu_mount_conf_value() {
    [ -r "$1" ] || return 0
    while IFS= read -r _zbv_line || [ -n "$_zbv_line" ]; do
        case "$_zbv_line" in "$2"=*) ;; *) continue ;; esac
        _zbv_value=${_zbv_line#*=}
        while :; do
            case "$_zbv_value" in
                *"$_ZIYU_BACKEND_CR"*) _zbv_value=${_zbv_value%%"$_ZIYU_BACKEND_CR"*}${_zbv_value#*"$_ZIYU_BACKEND_CR"} ;;
                *) break ;;
            esac
        done
        printf '%s' "$_zbv_value"
        return 0
    done < "$1"
    return 0
}

_ziyu_backend_state_clear() {
    ZIYU_BACKEND_STATE_LOADED=0
    ZIYU_BACKEND_SCHEMA=''
    ZIYU_BACKEND_BOOT_ID=''
    ZIYU_BACKEND_ROOT_MANAGER=''
    ZIYU_BACKEND_ROOT_VERSION=''
    ZIYU_BACKEND_ROOT_VERSION_CODE=''
    ZIYU_BACKEND_ROOT_DETECTION_SOURCE=''
    ZIYU_BACKEND_META_VERSION=''
    ZIYU_BACKEND_META_HYBRID_MODE=''
    ZIYU_BACKEND_META_ENGINE=''
    ZIYU_BACKEND_META_AVAILABLE=''
    ZIYU_BACKEND_META_ENABLED=''
    ZIYU_BACKEND_META_USABLE=''
    ZIYU_BACKEND_META_READY=''
    ZIYU_BACKEND_META_USABLE_REASON=''
    ZIYU_BACKEND_META_CLEANUP_CAPABILITY=''
    ZIYU_BACKEND_META_ACTIVE_DIR=''
    ZIYU_BACKEND_META_MODULE_DIR=''
    ZIYU_BACKEND_META_DETECTION_CHECKS=''
    ZIYU_BACKEND_PROVIDER_STATE=''
    ZIYU_BACKEND_PROVIDER_ID=''
    ZIYU_BACKEND_PROVIDER_LAYOUT=''
    ZIYU_BACKEND_PROVIDER_REASON=''
    ZIYU_BACKEND_PROVIDER_CONTENT_ROOT=''
    ZIYU_BACKEND_NOMOUNT_KERNEL_USABLE=''
    ZIYU_BACKEND_PREFERRED_BACKEND=''
    ZIYU_BACKEND_PREFERENCE_FAILURE=''
    ZIYU_BACKEND_SELECTED_BACKEND=''
    ZIYU_BACKEND_SELECTED_SELF_BACKEND=''
    ZIYU_BACKEND_ACTIVE_SELF_BACKEND=''
    ZIYU_BACKEND_ACTIVE_BACKEND=''
    ZIYU_BACKEND_PAYLOAD_FONT=''
    ZIYU_BACKEND_PAYLOAD_MANIFEST_SHA256=''
    ZIYU_BACKEND_BACKEND_CONFLICT=''
    ZIYU_BACKEND_FALLBACK_USED=''
    ZIYU_BACKEND_FALLBACK_REASON=''
    ZIYU_BACKEND_FALLBACK_SERVICE_RETRY=''
    ZIYU_BACKEND_META_RESULT=''
    ZIYU_BACKEND_SELF_RESULT=''
    ZIYU_BACKEND_MOUNT_STAGE=''
    ZIYU_BACKEND_VERIFICATION=''
    ZIYU_BACKEND_LAST_ERROR=''
    ZIYU_BACKEND_MOUNT_WARNING=''
    ZIYU_BACKEND_TIME=''
}

ziyu_backend_state_load() {
    ZIYU_BACKEND_STATE_FILE="$1"
    _ziyu_backend_state_clear
    [ -r "$ZIYU_BACKEND_STATE_FILE" ] || return 1
    _zbs_seen=''
    while IFS= read -r _zbs_line || [ -n "$_zbs_line" ]; do
        case "$_zbs_line" in *=*) ;; *) continue ;; esac
        _zbs_key=${_zbs_line%%=*}
        case "$_zbs_key" in
            schema|boot_id|root_manager|root_version|root_version_code|root_detection_source|meta_version|meta_hybrid_mode|\
            meta_engine|meta_available|meta_enabled|meta_usable|meta_ready|meta_usable_reason|meta_cleanup_capability|meta_active_dir|\
            meta_module_dir|meta_detection_checks|provider_state|provider_id|provider_layout|provider_reason|provider_content_root|nomount_kernel_usable|\
            preferred_backend|preference_failure|selected_backend|selected_self_backend|active_self_backend|active_backend|payload_font|payload_manifest_sha256|\
            backend_conflict|fallback_used|fallback_reason|fallback_service_retry|meta_result|self_result|mount_stage|verification|\
            last_error|mount_warning|time) ;;
            *) continue ;;
        esac
        case "|$_zbs_seen" in *"|$_zbs_key|"*) continue ;; esac
        _zbs_seen="$_zbs_seen$_zbs_key|"
        _zbs_value=${_zbs_line#*=}
        while :; do
            case "$_zbs_value" in
                *"$_ZIYU_BACKEND_CR"*) _zbs_value=${_zbs_value%%"$_ZIYU_BACKEND_CR"*}${_zbs_value#*"$_ZIYU_BACKEND_CR"} ;;
                *) break ;;
            esac
        done
        case "$_zbs_key" in
            schema) ZIYU_BACKEND_SCHEMA=$_zbs_value ;;
            boot_id) ZIYU_BACKEND_BOOT_ID=$_zbs_value ;;
            root_manager) ZIYU_BACKEND_ROOT_MANAGER=$_zbs_value ;;
            root_version) ZIYU_BACKEND_ROOT_VERSION=$_zbs_value ;;
            root_version_code) ZIYU_BACKEND_ROOT_VERSION_CODE=$_zbs_value ;;
            root_detection_source) ZIYU_BACKEND_ROOT_DETECTION_SOURCE=$_zbs_value ;;
            meta_version) ZIYU_BACKEND_META_VERSION=$_zbs_value ;;
            meta_hybrid_mode) ZIYU_BACKEND_META_HYBRID_MODE=$_zbs_value ;;
            meta_engine) ZIYU_BACKEND_META_ENGINE=$_zbs_value ;;
            meta_available) ZIYU_BACKEND_META_AVAILABLE=$_zbs_value ;;
            meta_enabled) ZIYU_BACKEND_META_ENABLED=$_zbs_value ;;
            meta_usable) ZIYU_BACKEND_META_USABLE=$_zbs_value ;;
            meta_ready) ZIYU_BACKEND_META_READY=$_zbs_value ;;
            meta_usable_reason) ZIYU_BACKEND_META_USABLE_REASON=$_zbs_value ;;
            meta_cleanup_capability) ZIYU_BACKEND_META_CLEANUP_CAPABILITY=$_zbs_value ;;
            meta_active_dir) ZIYU_BACKEND_META_ACTIVE_DIR=$_zbs_value ;;
            meta_module_dir) ZIYU_BACKEND_META_MODULE_DIR=$_zbs_value ;;
            meta_detection_checks) ZIYU_BACKEND_META_DETECTION_CHECKS=$_zbs_value ;;
            provider_state) ZIYU_BACKEND_PROVIDER_STATE=$_zbs_value ;;
            provider_id) ZIYU_BACKEND_PROVIDER_ID=$_zbs_value ;;
            provider_layout) ZIYU_BACKEND_PROVIDER_LAYOUT=$_zbs_value ;;
            provider_reason) ZIYU_BACKEND_PROVIDER_REASON=$_zbs_value ;;
            provider_content_root) ZIYU_BACKEND_PROVIDER_CONTENT_ROOT=$_zbs_value ;;
            nomount_kernel_usable) ZIYU_BACKEND_NOMOUNT_KERNEL_USABLE=$_zbs_value ;;
            preferred_backend) ZIYU_BACKEND_PREFERRED_BACKEND=$_zbs_value ;;
            preference_failure) ZIYU_BACKEND_PREFERENCE_FAILURE=$_zbs_value ;;
            selected_backend) ZIYU_BACKEND_SELECTED_BACKEND=$_zbs_value ;;
            selected_self_backend) ZIYU_BACKEND_SELECTED_SELF_BACKEND=$_zbs_value ;;
            active_self_backend) ZIYU_BACKEND_ACTIVE_SELF_BACKEND=$_zbs_value ;;
            active_backend) ZIYU_BACKEND_ACTIVE_BACKEND=$_zbs_value ;;
            payload_font) ZIYU_BACKEND_PAYLOAD_FONT=$_zbs_value ;;
            payload_manifest_sha256) ZIYU_BACKEND_PAYLOAD_MANIFEST_SHA256=$_zbs_value ;;
            backend_conflict) ZIYU_BACKEND_BACKEND_CONFLICT=$_zbs_value ;;
            fallback_used) ZIYU_BACKEND_FALLBACK_USED=$_zbs_value ;;
            fallback_reason) ZIYU_BACKEND_FALLBACK_REASON=$_zbs_value ;;
            fallback_service_retry) ZIYU_BACKEND_FALLBACK_SERVICE_RETRY=$_zbs_value ;;
            meta_result) ZIYU_BACKEND_META_RESULT=$_zbs_value ;;
            self_result) ZIYU_BACKEND_SELF_RESULT=$_zbs_value ;;
            mount_stage) ZIYU_BACKEND_MOUNT_STAGE=$_zbs_value ;;
            verification) ZIYU_BACKEND_VERIFICATION=$_zbs_value ;;
            last_error) ZIYU_BACKEND_LAST_ERROR=$_zbs_value ;;
            mount_warning) ZIYU_BACKEND_MOUNT_WARNING=$_zbs_value ;;
            time) ZIYU_BACKEND_TIME=$_zbs_value ;;
        esac
    done < "$ZIYU_BACKEND_STATE_FILE" 2>/dev/null || { _ziyu_backend_state_clear; return 1; }
    ZIYU_BACKEND_STATE_LOADED=1
    return 0
}
