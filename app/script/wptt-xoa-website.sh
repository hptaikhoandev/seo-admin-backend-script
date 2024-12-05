
#!/bin/bash

. /etc/wptt/.wptt.conf
if [[ $ngon_ngu = '' ]];then
	ngon_ngu='vi'
fi
. /etc/wptt/lang/$ngon_ngu.sh

NAME=$1
doi_so=$1

# Kiểm tra nếu cả NAME và NAME2 tồn tại
pathcheck_name1="/etc/wptt/vhost/.$NAME.conf"

if [[ -f "$pathcheck_name1" ]]; then
  echo "Error: Tên miền $NAME đều tồn tại trên hệ thống" >&2
  exit 1
fi

# Kiểm tra nếu $NAME không hợp lệ hoặc không tồn tại
if [[ "$NAME" = "0" || "$NAME" = "" ]]; then
  echo "Error: Tên miền không hợp lệ hoặc không được cung cấp." >&2
  exit 1
fi

pathcheck="/etc/wptt/vhost/.$NAME.conf"
if [[ ! -f "$pathcheck" ]]; then
  echo "Error: Tên miền $NAME không tồn tại trên hệ thống này." >&2
  exit 1
fi

if [[ $doi_so = '98' ]];then
doi_so=''
fi

if [[ $NAME = '98' ]];then
NAME=''
fi

if [[ $NAME = '' ]];then
echo ""
echo ""
echo ""
echo "========================================================================="
echo "|$quan_ly_domain => $xoa Website                                          |"
echo "========================================================================="
echo ""
echo ""
. /etc/wptt/tenmien
echo "$lua_chon_website_ban_muon $xoa:"
echo ""
lua_chon_NAME

fi

path="/etc/wptt/vhost/.$NAME.conf"


if [[ "$NAME" = "0" || "$NAME" = "" ]]; then
	. /etc/wptt/wptt-domain-main 1
fi

pathcheck="/etc/wptt/vhost/.$NAME.conf"
if [[ ! -f "$pathcheck" ]]; then
	clear
	. /etc/wptt/echo-color
	echoDo "$ten_mien_nay_khong_ton_tai_tren_he_thong"
	sleep 2
	. /etc/wptt/wptt-domain-main 1
	exit
fi


. /etc/wptt/vhost/."$NAME".conf
. /etc/wptt/.wptt.conf
. /etc/wptt/echo-color

CLEAN="$NAME"

if [[ $doi_so = '' ]];then
echo "$xac_nhan $xoa website $CLEAN?: "
prompt="$nhap_lua_chon_cua_ban [1-2]: "
dongy="n"
options=("$dong_y" "$khong_dong_y")
PS3="$prompt"
select opt in "${options[@]}"; do
	case "$REPLY" in
		1)
			dongy="y"
			break
			;;

		2)
			dongy="n"
			break
			;;

		$((${#options[@]} + 1)))
			printf "\nBạn nhập sai hệ thống sẽ chọn là không đồng ý\n"
			break
			;;
		*)
			printf "Bạn nhập sai hệ thống sẽ chọn là không đồng ý\n"
			break
			;;
	esac
done
else
dongy='y'
fi

if [[ "$dongy" = "y" ]]; then

	if [[ "$NAME" = "$Website_chinh" ]]; then
		echo ""
		echo ""
		echo "$NAME là website chính đại diện cho websever của bạn hãy lựa chọn domain khac để thay thế làm website chính:"
		echo "lựa chọn domain chính khác: "
		echo ""
		NAME3="$NAME"
		echo "Ghi chú: Chon 1 domain khác đã được kích hoạt SSL"
		echo ""
		mkdir -p /etc/wptt/vhost2
		if [ "$(ls -A /etc/wptt/vhost)" ]; then
			for entry in $(ls -A /etc/wptt/vhost); do
				domain=$(echo $entry | sed 's/^.//' | sed 's/.conf//')
				path="/usr/local/lsws/$domain/html"
				i=1

				if [[ -d "$path" ]]; then
					cp -f /etc/wptt/vhost/."$domain".conf /etc/wptt/vhost2
				fi
			done
		fi

		rm -f /etc/wptt/vhost2/."$Website_chinh".conf

		#check điều kiện số lượng website, nếu website chỉ có 1 domain là domain chính thì sẽ báo lỗi
		check_so_luong_website=$(ls -A /etc/wptt/vhost2 | wc -l)
		if [[ $check_so_luong_website = '0' ]];then
			echoDo "Bạn không thể xoá website khi hệ thống chỉ có 1 domain duy nhất là domain chính"
			echoDo "Nếu bạn muốn xoá website thì vui lòng thêm 1 website vào rồi hãy xoá website này đi"
			rm -rf /etc/wptt/vhost2
			check_menu_wptangtoc_active=$1
			if [[ $check_menu_wptangtoc_active = "98" ]];then
				. /etc/wptt/wptt-domain-main 1
			fi
			return 2>/dev/null;exit
		fi


		function lua_chon_NAME_vhost2() {
			NAME=""
			if [ "$(ls -At /etc/wptt/vhost2)" ]; then
				selects=()
				for entry in $(ls -A /etc/wptt/vhost2); do
					NAME=$(echo $entry | sed 's/^.//' | sed 's/.conf//')
					if [ "$NAME" != "${NAME/./}" ]; then
						selects+=("$NAME")
					fi
				done

				if [[ $selects = '' ]];then
					echoDo "Không thể xóa website chính khi không có website khác thay thế làm website đại diện"
					echo "Vui lòng thêm website một website khác rồi xóa website $Website_chinh, rồi ủy đại diện cho website mới đó"
					. /etc/wptt/wptt-domain-main 1
				fi

				PS3="
$(tput setab 0)-//- $nhap_lua_chon_cua_ban [0=$exit_thoat]:$(tput sgr0) "
				select select in ${selects[@]}; do
					NAME=$select
					index=$REPLY
					break
				done
			else
				clear
				echo "$khong_co_domain_nao_ton_tai_tren_he_thong"
				exit
			fi
		}
	lua_chon_NAME_vhost2
	NAMEPHU="$NAME"
	if [[ "$NAMEPHU" = "$Website_chinh" ]]; then
		echoDo "Thong bao loi"
		echoDo "Trung lap website chinh va website thay the chinh: $NAME3"
		echo ""
		echo ""
		echo "Vui long xoa lai website"
		. /etc/wptt/wptt-domain-main 1
		exit
	fi
	if [[ "$NAMEPHU" = "0" || "$NAMEPHU" = "" ]]; then
		. /etc/wptt/wptt-domain-main 1
		exit
	fi

	_runing "Chuyển đổi website chính từ $CLEAN thành $NAMEPHU"
	sed -i "/keyFile/d" /usr/local/lsws/conf/httpd_config.conf
	sed -i "/certFile/d" /usr/local/lsws/conf/httpd_config.conf
	sed -i "/CACertFile/d" /usr/local/lsws/conf/httpd_config.conf
	sed -i "/https/a keyFile              \/etc\/letsencrypt\/live\/$NAMEPHU\/privkey.pem" /usr/local/lsws/conf/httpd_config.conf
	sed -i "/https/a certFile             \/etc\/letsencrypt\/live\/$NAMEPHU\/cert.pem" /usr/local/lsws/conf/httpd_config.conf
	sed -i "/https/a CACertFile           \/etc\/letsencrypt\/live\/$NAMEPHU\/chain.pem" /usr/local/lsws/conf/httpd_config.conf
	/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1
	sed -i "/$Website_chinh/d" /etc/wptt/.wptt.conf
	echo "Website_chinh=$NAMEPHU" >>/etc/wptt/.wptt.conf
	rm -rf /etc/wptt/vhost2
	if [[ $id_dang_nhap_phpmyadmin ]]; then
		cp -rf /usr/local/lsws/"$CLEAN"/html/phpmyadmin /usr/local/lsws/"$NAMEPHU"/html/
		mkdir -p /usr/local/lsws/"$NAMEPHU"/passwd
		cp -f /usr/local/lsws/"$Website_chinh"/passwd/.phpmyadmin /usr/local/lsws/"$NAMEPHU"/passwd

		#tuong thich ubuntu tuong thich nhom litespeed
if $(cat /etc/*release | grep -q "Ubuntu") ; then
tuong_thich_nhom_litespeed="nogroup"
else
tuong_thich_nhom_litespeed="nobody"
fi

		chown -R nobody:$tuong_thich_nhom_litespeed /usr/local/lsws/"$NAMEPHU"/passwd
		echo 'realm '${NAMEPHU}phpphpmyadmin' {
		userDB  {
		location              /usr/local/lsws/'$NAMEPHU'/passwd/.phpmyadmin
	}
}
context /phpmyadmin/ {
location                phpmyadmin/
allowBrowse             1
realm                   '${NAMEPHU}phpphpmyadmin'

accessControl  {
allow                 ALL
}

rewrite  {

}
addDefaultCharset	  off

phpIniOverride  {

}
}' >>/usr/local/lsws/conf/vhosts/"$NAMEPHU"/"$NAMEPHU".conf

	fi
	_rundone "Chuyển đổi website chính từ $CLEAN thành $NAMEPHU"
	fi

		#xóa database website
		_runing "$xoa database website $CLEAN"
		#kill user, để trong một số trường hợp bị kẹt sql, sẽ kill database rồi xoá website
		mariadb -u $database_admin_username -p"$database_admin_password" -e "KILL USER ${DB_User_web}"

		#xoá database
		mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP DATABASE ${DB_Name_web}"

		#xoá user database
		mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP USER '${DB_User_web}'@'localhost'"

		#tiến hành xóa database của subfolder website
		if [[ $subfolder_su_dung ]];then
			if [[ -d /etc/wptt/$CLEAN-wptt ]];then
				query_sub=($(ls -At /etc/wptt/$CLEAN-wptt))
				for subfolder in ${query_sub[@]};do
					. /etc/wptt/$CLEAN-wptt/$subfolder
					mariadb -u $database_admin_username -p"$database_admin_password" -e "DROP DATABASE ${DB_Name_web}"
				done
			fi

			rm -rf /etc/wptt/$CLEAN-wptt/$subfolder
			# trả lại biến website chính
			. /etc/wptt/vhost/."$CLEAN".conf
		fi

		_runing "$xoa database website $CLEAN"
		_runing "$xoa website $CLEAN $tren_he_thong"
		rm -rf /usr/local/lsws/conf/vhosts/"$CLEAN"
		if [[ $User_name_vhost ]];then
			pkill -u $User_name_vhost >/dev/null 2>&1
			usermod -R wptangtoc-ols "$User_name_vhost" >/dev/null 2>&1
			userdel -f "$User_name_vhost" >/dev/null 2>&1
			if [[ -d /home/$User_name_vhost ]];then
				rm -rf /home/$User_name_vhost
			fi
		fi

		rm -rf /wptangtoc-ols/"$CLEAN"
		rm -rf /usr/local/lsws/"$CLEAN"
		rm -rf /home/"$CLEAN"

	#xóa maps cổng port
	sed -i "/$CLEAN $CLEAN/d" /usr/local/lsws/conf/httpd_config.conf

	#xoa vhost theo block
	sed -i -e '/^virtualhost '$CLEAN'/,/^}$/d' /usr/local/lsws/conf/httpd_config.conf 
	# sed -i "/$CLEAN/,+10d" /usr/local/lsws/conf/httpd_config.conf

	rm -f /etc/wptt/vhost/.$CLEAN.conf

	_rundone "$xoa website $CLEAN $tren_he_thong"

    _runing "Xóa chứng chỉ SSL website $CLEAN"
    certbot revoke --non-interactive --agree-tos --cert-path /etc/letsencrypt/live/$CLEAN/cert.pem >/dev/null 2>&1
    rm -rf /etc/letsencrypt/live/"$CLEAN"
    _rundone "Xóa chứng chỉ SSL website $CLEAN"


	if [[ -f /etc/wptt-auto/$CLEAN-auto-backup ]];then
		_runing "$xoa $tu_dong_sao_luu_website $CLEAN"
		rm -f /etc/wptt-auto/$CLEAN-auto-backup
		rm -f /etc/cron.d/backup$CLEAN.cron
		_rundone "$xoa $tu_dong_sao_luu_website $CLEAN"
	fi

	if [[ -f /etc/cron.d/delete-google-driver-$CLEAN.cron ]];then
		_runing "Xóa tự động xóa file backup website $CLEAN trên Google Driver hết hạn" 
		rm -f /etc/cron.d/delete-google-driver-$CLEAN.cron
		rm -f /etc/wptt-auto/$CLEAN-delete-backup-google-driver
		_rundone "Xóa tự động xóa file backup website $CLEAN trên Google Driver hết hạn" 
	fi


	if [[ -f /etc/cron.d/delete$CLEAN.cron ]];then
		_runing "Xóa tự động xóa file backup website $CLEAN hết hạn" 
		rm -f /etc/cron.d/delete$CLEAN.cron
		rm -f /etc/wptt-auto/$CLEAN-delete-backup
		_rundone "Xóa tự động xóa file backup website $CLEAN hết hạn" 
	fi


if [[ -f /etc/wptt/chuyen-huong/.$CLEAN.conf ]];then
	rm -f /etc/wptt/chuyen-huong/.$CLEAN.conf
fi


NAMEwpadmin=${CLEAN//[-._]/wp}
if [[ -f /etc/fail2ban/filter.d/wordpress-dangnhap-$NAMEwpadmin.conf ]];then
rm -f /etc/fail2ban/filter.d/wordpress-dangnhap-$NAMEwpadmin.conf
sed -i "/wordpress-dangnhap-$NAMEwpadmin/,+8d" /etc/fail2ban/jail.local
fi

if [[ -f /etc/fail2ban/filter.d/ddos-$NAMEwpadmin.conf ]]; then
	_runing "Xoá thiết lập chống ddos website $CLEAN"
	. /etc/wptt/bao-mat/wptt-canh-bao-ddos-thiet-lap-xoa $CLEAN >/dev/null 2>&1
	_rundone "Xoá thiết lập chống ddos website $CLEAN"
fi


	sleep 2
	echo "==================================================================="
	echo "Đã xóa thành công website $CLEAN                 "
	echo "==================================================================="

fi


check_menu_wptangtoc_active=$1
if [[ $check_menu_wptangtoc_active = "98" ]];then
	. /etc/wptt/wptt-domain-main 1
fi
