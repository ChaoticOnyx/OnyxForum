-- --------------------------------------------------------
-- Хост:                         149.202.74.230
-- Версия сервера:               8.0.27-0ubuntu0.21.04.1 - (Ubuntu)
-- Операционная система:         Linux
-- HeidiSQL Версия:              11.2.0.6213
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Дамп структуры базы данных chaotic
CREATE DATABASE IF NOT EXISTS `chaotic` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `chaotic`;

-- Дамп структуры для таблица chaotic.blacklist_ip
CREATE TABLE IF NOT EXISTS `blacklist_ip` (
  `ip` int NOT NULL,
  PRIMARY KEY (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.ckey_computerid
CREATE TABLE IF NOT EXISTS `ckey_computerid` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `computerid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ckey` (`ckey`),
  KEY `computerid` (`computerid`)
) ENGINE=InnoDB AUTO_INCREMENT=276106 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.ckey_ip
CREATE TABLE IF NOT EXISTS `ckey_ip` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ckey` (`ckey`) USING BTREE,
  KEY `computerid` (`ip`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=276106 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.connection
CREATE TABLE IF NOT EXISTS `connection` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime DEFAULT NULL,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `computerid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102190 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.eams_ban_provider
CREATE TABLE IF NOT EXISTS `eams_ban_provider` (
  `ip_as` varchar(255) NOT NULL,
  `ip_isp` varchar(255) NOT NULL,
  `ip_org` varchar(255) NOT NULL,
  `ip_country` varchar(255) NOT NULL,
  `ip_countryCode` varchar(255) NOT NULL,
  `ip_region` varchar(255) NOT NULL,
  `ip_regionCode` varchar(255) NOT NULL,
  `ip_city` varchar(255) NOT NULL,
  `ip_lat` float(7,2) NOT NULL,
  `ip_lon` float(7,2) NOT NULL,
  `ip_timezone` varchar(255) NOT NULL,
  `ip_zip` varchar(255) NOT NULL,
  `ip_reverse` varchar(255) NOT NULL,
  `ip_mobile` bit(1) NOT NULL,
  `ip_proxy` bit(1) NOT NULL,
  `type` bit(1) NOT NULL,
  `priority` bit(1) NOT NULL,
  `ckey` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COMMENT='1';

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.eams_cache
CREATE TABLE IF NOT EXISTS `eams_cache` (
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `response` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_admin
CREATE TABLE IF NOT EXISTS `erro_admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `rank` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'Administrator',
  `flags` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQUE` (`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=440 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_ban
CREATE TABLE IF NOT EXISTS `erro_ban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `serverip` varchar(32) NOT NULL,
  `bantype` varchar(32) NOT NULL,
  `reason` text NOT NULL,
  `job` varchar(32) DEFAULT NULL,
  `duration` int NOT NULL,
  `rounds` int DEFAULT NULL,
  `expiration_time` datetime NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `computerid` varchar(32) NOT NULL,
  `ip` varchar(32) NOT NULL,
  `a_ckey` varchar(32) NOT NULL,
  `a_computerid` varchar(32) NOT NULL,
  `a_ip` varchar(32) NOT NULL,
  `who` text NOT NULL,
  `adminwho` text NOT NULL,
  `edits` text,
  `unbanned` tinyint(1) DEFAULT NULL,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_reason` text,
  `unbanned_ckey` varchar(32) DEFAULT NULL,
  `unbanned_computerid` varchar(32) DEFAULT NULL,
  `unbanned_ip` varchar(32) DEFAULT NULL,
  `server_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`,`server_id`)
) ENGINE=InnoDB AUTO_INCREMENT=91043 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_ban_latin1
CREATE TABLE IF NOT EXISTS `erro_ban_latin1` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `serverip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bantype` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `reason` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `job` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `duration` int NOT NULL,
  `rounds` int DEFAULT NULL,
  `expiration_time` datetime NOT NULL,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `who` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `adminwho` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `edits` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  `unbanned` tinyint(1) DEFAULT NULL,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_reason` text,
  `unbanned_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `server_id` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  PRIMARY KEY (`id`,`server_id`)
) ENGINE=InnoDB AUTO_INCREMENT=82227 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_iaa_approved
CREATE TABLE IF NOT EXISTS `erro_iaa_approved` (
  `ckey` varchar(32) NOT NULL,
  `approvals` int DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_iaa_jobban
CREATE TABLE IF NOT EXISTS `erro_iaa_jobban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fakeid` varchar(6) NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `iaa_ckey` varchar(32) NOT NULL,
  `other_ckeys` text NOT NULL,
  `reason` text NOT NULL,
  `job` varchar(32) NOT NULL,
  `creation_time` datetime NOT NULL,
  `resolve_time` datetime DEFAULT NULL,
  `resolve_comment` text,
  `resolve_ckey` varchar(32) DEFAULT NULL,
  `cancel_time` datetime DEFAULT NULL,
  `cancel_comment` text,
  `cancel_ckey` varchar(32) DEFAULT NULL,
  `status` varchar(32) NOT NULL,
  `expiration_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_player
CREATE TABLE IF NOT EXISTS `erro_player` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `firstseen` datetime NOT NULL,
  `lastseen` datetime NOT NULL,
  `ip` varchar(18) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `lastadminrank` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'Player',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ckey` (`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=40322 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_watch
CREATE TABLE IF NOT EXISTS `erro_watch` (
  `ckey` varchar(32) NOT NULL,
  `reason` text NOT NULL,
  `adminckey` varchar(32) NOT NULL,
  `timestamp` datetime NOT NULL,
  `last_editor` varchar(32) DEFAULT NULL,
  `edits` text,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.erro_watch_latin1
CREATE TABLE IF NOT EXISTS `erro_watch_latin1` (
  `ckey` varchar(32) NOT NULL,
  `reason` text NOT NULL,
  `adminckey` varchar(32) NOT NULL,
  `timestamp` datetime NOT NULL,
  `last_editor` varchar(32) DEFAULT NULL,
  `edits` text,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.ip2nation
CREATE TABLE IF NOT EXISTS `ip2nation` (
  `ip` int unsigned NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT '',
  KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.ip2nationCountries
CREATE TABLE IF NOT EXISTS `ip2nationCountries` (
  `code` varchar(4) NOT NULL DEFAULT '',
  `iso_code_2` varchar(2) NOT NULL DEFAULT '',
  `iso_code_3` varchar(3) DEFAULT '',
  `iso_country` varchar(255) NOT NULL DEFAULT '',
  `country` varchar(255) NOT NULL DEFAULT '',
  `lat` float NOT NULL DEFAULT '0',
  `lon` float NOT NULL DEFAULT '0',
  PRIMARY KEY (`code`),
  KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.library
CREATE TABLE IF NOT EXISTS `library` (
  `id` int NOT NULL AUTO_INCREMENT,
  `author` text NOT NULL,
  `title` text NOT NULL,
  `content` text NOT NULL,
  `category` text NOT NULL,
  `deleted` int DEFAULT NULL,
  `author_ckey` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=912 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.library_latin1
CREATE TABLE IF NOT EXISTS `library_latin1` (
  `id` int NOT NULL AUTO_INCREMENT,
  `author` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `title` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `content` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `category` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `deleted` int DEFAULT NULL,
  `author_ckey` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=623 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.old_erro_ban
CREATE TABLE IF NOT EXISTS `old_erro_ban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `serverip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bantype` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `reason` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `job` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `duration` int NOT NULL,
  `rounds` int DEFAULT NULL,
  `expiration_time` datetime NOT NULL,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `who` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `adminwho` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `edits` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  `unbanned` tinyint(1) DEFAULT NULL,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_reason` text,
  `unbanned_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14581 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.serverids
CREATE TABLE IF NOT EXISTS `serverids` (
  `server_id` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  PRIMARY KEY (`server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.whitelist
CREATE TABLE IF NOT EXISTS `whitelist` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` text NOT NULL,
  `race` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.whitelist_ckey
CREATE TABLE IF NOT EXISTS `whitelist_ckey` (
  `ckey` varchar(50) NOT NULL,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.Z_buys
CREATE TABLE IF NOT EXISTS `Z_buys` (
  `_id` int NOT NULL AUTO_INCREMENT,
  `byond` varchar(32) NOT NULL,
  `type` varchar(100) NOT NULL,
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB AUTO_INCREMENT=733 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица chaotic.Z_donators
CREATE TABLE IF NOT EXISTS `Z_donators` (
  `byond` varchar(32) NOT NULL DEFAULT '',
  `sum` float(7,2) NOT NULL DEFAULT '0.00',
  `current` float(7,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`byond`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.


-- Дамп структуры базы данных eos
CREATE DATABASE IF NOT EXISTS `eos` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `eos`;

-- Дамп структуры для таблица eos.ckey_computerid
CREATE TABLE IF NOT EXISTS `ckey_computerid` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `computerid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ckey` (`ckey`),
  KEY `computerid` (`computerid`)
) ENGINE=InnoDB AUTO_INCREMENT=31537 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.ckey_ip
CREATE TABLE IF NOT EXISTS `ckey_ip` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ckey` (`ckey`) USING BTREE,
  KEY `computerid` (`ip`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=31537 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.connection
CREATE TABLE IF NOT EXISTS `connection` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime DEFAULT NULL,
  `ckey` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `computerid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47511 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.eams_cache
CREATE TABLE IF NOT EXISTS `eams_cache` (
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `response` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_admin
CREATE TABLE IF NOT EXISTS `erro_admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `rank` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'Administrator',
  `flags` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQUE` (`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=399 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_ban
CREATE TABLE IF NOT EXISTS `erro_ban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `serverip` varchar(32) NOT NULL,
  `bantype` varchar(32) NOT NULL,
  `reason` text NOT NULL,
  `job` varchar(32) DEFAULT NULL,
  `duration` int NOT NULL,
  `rounds` int DEFAULT NULL,
  `expiration_time` datetime NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `computerid` varchar(32) NOT NULL,
  `ip` varchar(32) NOT NULL,
  `a_ckey` varchar(32) NOT NULL,
  `a_computerid` varchar(32) NOT NULL,
  `a_ip` varchar(32) NOT NULL,
  `who` text NOT NULL,
  `adminwho` text NOT NULL,
  `edits` text,
  `unbanned` tinyint(1) DEFAULT NULL,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_reason` text,
  `unbanned_ckey` varchar(32) DEFAULT NULL,
  `unbanned_computerid` varchar(32) DEFAULT NULL,
  `unbanned_ip` varchar(32) DEFAULT NULL,
  `server_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`,`server_id`)
) ENGINE=InnoDB AUTO_INCREMENT=89148 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_iaa_approved
CREATE TABLE IF NOT EXISTS `erro_iaa_approved` (
  `ckey` varchar(32) NOT NULL,
  `approvals` int DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_iaa_jobban
CREATE TABLE IF NOT EXISTS `erro_iaa_jobban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fakeid` varchar(6) NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `iaa_ckey` varchar(32) NOT NULL,
  `other_ckeys` text NOT NULL,
  `reason` text NOT NULL,
  `job` varchar(32) NOT NULL,
  `creation_time` datetime NOT NULL,
  `resolve_time` datetime DEFAULT NULL,
  `resolve_comment` text,
  `resolve_ckey` varchar(32) DEFAULT NULL,
  `cancel_time` datetime DEFAULT NULL,
  `cancel_comment` text,
  `cancel_ckey` varchar(32) DEFAULT NULL,
  `status` varchar(32) NOT NULL,
  `expiration_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_player
CREATE TABLE IF NOT EXISTS `erro_player` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `firstseen` datetime NOT NULL,
  `lastseen` datetime NOT NULL,
  `ip` varchar(18) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `lastadminrank` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'Player',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ckey` (`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=33106 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.erro_watch
CREATE TABLE IF NOT EXISTS `erro_watch` (
  `ckey` varchar(32) NOT NULL,
  `reason` text NOT NULL,
  `adminckey` varchar(32) NOT NULL,
  `timestamp` datetime NOT NULL,
  `last_editor` varchar(32) DEFAULT NULL,
  `edits` text,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.ip2nation
CREATE TABLE IF NOT EXISTS `ip2nation` (
  `ip` int unsigned NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT '',
  KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.ip2nationCountries
CREATE TABLE IF NOT EXISTS `ip2nationCountries` (
  `code` varchar(4) NOT NULL DEFAULT '',
  `iso_code_2` varchar(2) NOT NULL DEFAULT '',
  `iso_code_3` varchar(3) DEFAULT '',
  `iso_country` varchar(255) NOT NULL DEFAULT '',
  `country` varchar(255) NOT NULL DEFAULT '',
  `lat` float NOT NULL DEFAULT '0',
  `lon` float NOT NULL DEFAULT '0',
  PRIMARY KEY (`code`),
  KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.library
CREATE TABLE IF NOT EXISTS `library` (
  `id` int NOT NULL AUTO_INCREMENT,
  `author` text NOT NULL,
  `title` text NOT NULL,
  `content` text NOT NULL,
  `category` text NOT NULL,
  `deleted` int DEFAULT NULL,
  `author_ckey` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=714 DEFAULT CHARSET=utf8mb3 ROW_FORMAT=COMPACT;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.old_erro_ban
CREATE TABLE IF NOT EXISTS `old_erro_ban` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `serverip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bantype` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `reason` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `job` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `duration` int NOT NULL,
  `rounds` int DEFAULT NULL,
  `expiration_time` datetime NOT NULL,
  `ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `a_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `who` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `adminwho` text CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `edits` text CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  `unbanned` tinyint(1) DEFAULT NULL,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_reason` text,
  `unbanned_ckey` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_computerid` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  `unbanned_ip` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14581 DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.serverids
CREATE TABLE IF NOT EXISTS `serverids` (
  `server_id` varchar(32) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  PRIMARY KEY (`server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.whitelist
CREATE TABLE IF NOT EXISTS `whitelist` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` text NOT NULL,
  `race` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица eos.whitelist_ckey
CREATE TABLE IF NOT EXISTS `whitelist_ckey` (
  `ckey` varchar(50) NOT NULL,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Экспортируемые данные не выделены.


-- Дамп структуры базы данных freerp
CREATE DATABASE IF NOT EXISTS `freerp` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `freerp`;

-- Дамп структуры для процедура freerp.set_poll_deleted
DELIMITER //
CREATE PROCEDURE `set_poll_deleted`(
	IN `poll_id` INT
)
    SQL SECURITY INVOKER
BEGIN
UPDATE `SS13_poll_question` SET deleted = 1 WHERE id = poll_id;
UPDATE `SS13_poll_option` SET deleted = 1 WHERE pollid = poll_id;
UPDATE `SS13_poll_vote` SET deleted = 1 WHERE pollid = poll_id;
UPDATE `SS13_poll_textreply` SET deleted = 1 WHERE pollid = poll_id;
END//
DELIMITER ;

-- Дамп структуры для таблица freerp.SS13_admin
CREATE TABLE IF NOT EXISTS `SS13_admin` (
  `ckey` varchar(32) NOT NULL,
  `rank` varchar(32) NOT NULL,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_admin_log
CREATE TABLE IF NOT EXISTS `SS13_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `round_id` int NOT NULL,
  `adminckey` varchar(32) NOT NULL,
  `adminip` int unsigned NOT NULL,
  `operation` enum('add admin','remove admin','change admin rank','add rank','remove rank','change rank flags') NOT NULL,
  `target` varchar(50) DEFAULT NULL,
  `log` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=432 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_admin_ranks
CREATE TABLE IF NOT EXISTS `SS13_admin_ranks` (
  `rank` varchar(32) NOT NULL,
  `flags` smallint unsigned NOT NULL,
  `exclude_flags` smallint unsigned NOT NULL,
  `can_edit_flags` smallint unsigned NOT NULL,
  PRIMARY KEY (`rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_ban
CREATE TABLE IF NOT EXISTS `SS13_ban` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `bantime` datetime NOT NULL,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `round_id` int unsigned NOT NULL,
  `role` varchar(32) DEFAULT NULL,
  `expiration_time` datetime DEFAULT NULL,
  `applies_to_admins` tinyint unsigned NOT NULL DEFAULT '0',
  `reason` varchar(2048) NOT NULL,
  `ckey` varchar(32) DEFAULT NULL,
  `ip` int unsigned DEFAULT NULL,
  `computerid` varchar(32) DEFAULT NULL,
  `a_ckey` varchar(32) NOT NULL,
  `a_ip` int unsigned NOT NULL,
  `a_computerid` varchar(32) NOT NULL,
  `who` varchar(2048) NOT NULL,
  `adminwho` varchar(2048) NOT NULL,
  `edits` text,
  `unbanned_datetime` datetime DEFAULT NULL,
  `unbanned_ckey` varchar(32) DEFAULT NULL,
  `unbanned_ip` int unsigned DEFAULT NULL,
  `unbanned_computerid` varchar(32) DEFAULT NULL,
  `unbanned_round_id` int unsigned DEFAULT NULL,
  `global_ban` tinyint unsigned NOT NULL DEFAULT '1',
  `hidden` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_ban_isbanned` (`ckey`,`role`,`unbanned_datetime`,`expiration_time`),
  KEY `idx_ban_isbanned_details` (`ckey`,`ip`,`computerid`,`role`,`unbanned_datetime`,`expiration_time`),
  KEY `idx_ban_count` (`bantime`,`a_ckey`,`applies_to_admins`,`unbanned_datetime`,`expiration_time`)
) ENGINE=InnoDB AUTO_INCREMENT=5144 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_characters
CREATE TABLE IF NOT EXISTS `SS13_characters` (
  `real_name` varchar(50) DEFAULT NULL,
  `name_is_always_random` bit(1) NOT NULL,
  `body_is_always_random` bit(1) NOT NULL,
  `gender` varchar(50) NOT NULL,
  `age` tinyint unsigned NOT NULL,
  `hair_color` varchar(50) NOT NULL,
  `facial_hair_color` varchar(50) NOT NULL,
  `eye_color` varchar(50) NOT NULL,
  `skin_tone` varchar(50) NOT NULL,
  `hair_style_name` varchar(50) NOT NULL,
  `facial_style_name` varchar(50) NOT NULL,
  `feature_ethcolor` varchar(50) NOT NULL,
  `underwear` varchar(50) NOT NULL,
  `undershirt` varchar(50) NOT NULL,
  `socks` varchar(50) NOT NULL,
  `backbag` varchar(50) NOT NULL,
  `uplink_loc` varchar(50) NOT NULL,
  `species` varchar(50) NOT NULL,
  `features` json NOT NULL,
  `joblessrole` smallint NOT NULL,
  `job_civlian_high` smallint NOT NULL,
  `job_civilian_med` smallint NOT NULL,
  `job_civilian_low` smallint NOT NULL,
  `job_medsci_high` smallint NOT NULL,
  `job_medsci_med` smallint NOT NULL,
  `job_medsci_low` smallint NOT NULL,
  `job_engsec_high` smallint NOT NULL,
  `job_engsec_med` smallint NOT NULL,
  `job_engsec_low` smallint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_connection_log
CREATE TABLE IF NOT EXISTS `SS13_connection_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime DEFAULT NULL,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `round_id` int unsigned NOT NULL,
  `ckey` varchar(45) DEFAULT NULL,
  `ip` int unsigned NOT NULL,
  `computerid` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=595274 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_death
CREATE TABLE IF NOT EXISTS `SS13_death` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pod` varchar(50) NOT NULL,
  `x_coord` smallint unsigned NOT NULL,
  `y_coord` smallint unsigned NOT NULL,
  `z_coord` smallint unsigned NOT NULL,
  `mapname` varchar(32) NOT NULL,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `round_id` int NOT NULL,
  `tod` datetime NOT NULL COMMENT 'Time of death',
  `job` varchar(32) NOT NULL,
  `special` varchar(32) DEFAULT NULL,
  `name` varchar(96) NOT NULL,
  `byondkey` varchar(32) NOT NULL,
  `laname` varchar(96) DEFAULT NULL,
  `lakey` varchar(32) DEFAULT NULL,
  `bruteloss` smallint unsigned NOT NULL,
  `brainloss` smallint unsigned NOT NULL,
  `fireloss` smallint unsigned NOT NULL,
  `oxyloss` smallint unsigned NOT NULL,
  `toxloss` smallint unsigned NOT NULL,
  `cloneloss` smallint unsigned NOT NULL,
  `staminaloss` smallint unsigned NOT NULL,
  `last_words` varchar(255) DEFAULT NULL,
  `suicide` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=244276 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_feedback
CREATE TABLE IF NOT EXISTS `SS13_feedback` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `round_id` int unsigned NOT NULL,
  `key_name` varchar(32) NOT NULL,
  `version` tinyint unsigned NOT NULL,
  `key_type` enum('text','amount','tally','nested tally','associative') NOT NULL,
  `json` json NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=276686 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_ipintel
CREATE TABLE IF NOT EXISTS `SS13_ipintel` (
  `ip` int unsigned NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `intel` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`ip`),
  KEY `idx_ipintel` (`ip`,`intel`,`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_legacy_population
CREATE TABLE IF NOT EXISTS `SS13_legacy_population` (
  `id` int NOT NULL AUTO_INCREMENT,
  `playercount` int DEFAULT NULL,
  `admincount` int DEFAULT NULL,
  `time` datetime NOT NULL,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `round_id` int unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73824 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_library
CREATE TABLE IF NOT EXISTS `SS13_library` (
  `id` int NOT NULL AUTO_INCREMENT,
  `author` varchar(45) NOT NULL,
  `title` varchar(45) NOT NULL,
  `content` text NOT NULL,
  `category` enum('Any','Fiction','Non-Fiction','Adult','Reference','Religion') NOT NULL,
  `ckey` varchar(32) NOT NULL DEFAULT 'LEGACY',
  `datetime` datetime NOT NULL,
  `deleted` tinyint unsigned DEFAULT NULL,
  `round_id_created` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `deleted_idx` (`deleted`),
  KEY `idx_lib_id_del` (`id`,`deleted`),
  KEY `idx_lib_del_title` (`deleted`,`title`),
  KEY `idx_lib_search` (`deleted`,`author`,`title`,`category`)
) ENGINE=InnoDB AUTO_INCREMENT=334 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_mentor
CREATE TABLE IF NOT EXISTS `SS13_mentor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ckey` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_mentor_memo
CREATE TABLE IF NOT EXISTS `SS13_mentor_memo` (
  `ckey` varchar(32) NOT NULL,
  `memotext` text NOT NULL,
  `timestamp` datetime NOT NULL,
  `last_editor` varchar(32) DEFAULT NULL,
  `edits` text,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_messages
CREATE TABLE IF NOT EXISTS `SS13_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` enum('memo','message','message sent','note','watchlist entry') NOT NULL,
  `targetckey` varchar(32) NOT NULL,
  `adminckey` varchar(32) NOT NULL,
  `text` varchar(2048) NOT NULL,
  `timestamp` datetime NOT NULL,
  `expire_timestamp` datetime DEFAULT NULL,
  `severity` text,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `round_id` int unsigned NOT NULL,
  `secret` tinyint unsigned NOT NULL,
  `lasteditor` varchar(32) DEFAULT NULL,
  `edits` text,
  `deleted` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_msg_ckey_time` (`targetckey`,`timestamp`,`deleted`),
  KEY `idx_msg_type_ckeys_time` (`type`,`targetckey`,`adminckey`,`timestamp`,`deleted`),
  KEY `idx_msg_type_ckey_time_odr` (`type`,`targetckey`,`timestamp`,`deleted`)
) ENGINE=InnoDB AUTO_INCREMENT=5191 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_metacoin_item_purchases
CREATE TABLE IF NOT EXISTS `SS13_metacoin_item_purchases` (
  `ckey` varchar(32) NOT NULL,
  `purchase_date` datetime NOT NULL,
  `item_id` varchar(50) NOT NULL,
  `item_class` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_player
CREATE TABLE IF NOT EXISTS `SS13_player` (
  `ckey` varchar(32) NOT NULL,
  `byond_key` varchar(32) NOT NULL DEFAULT 'Player',
  `firstseen` datetime NOT NULL,
  `firstseen_round_id` int unsigned NOT NULL,
  `lastseen` datetime NOT NULL,
  `lastseen_round_id` int unsigned NOT NULL,
  `ip` int unsigned NOT NULL,
  `computerid` varchar(32) NOT NULL,
  `uuid` varchar(64) DEFAULT NULL,
  `lastadminrank` varchar(32) NOT NULL DEFAULT 'Player',
  `accountjoindate` date DEFAULT NULL,
  `flags` smallint unsigned NOT NULL DEFAULT '0',
  `antag_tokens` tinyint unsigned DEFAULT '0',
  `metacoins` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`ckey`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `idx_player_cid_ckey` (`computerid`,`ckey`),
  KEY `idx_player_ip_ckey` (`ip`,`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_poll_option
CREATE TABLE IF NOT EXISTS `SS13_poll_option` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pollid` int NOT NULL,
  `text` varchar(255) NOT NULL,
  `minval` int DEFAULT NULL,
  `maxval` int DEFAULT NULL,
  `descmin` varchar(32) DEFAULT NULL,
  `descmid` varchar(32) DEFAULT NULL,
  `descmax` varchar(32) DEFAULT NULL,
  `default_percentage_calc` tinyint unsigned NOT NULL DEFAULT '1',
  `deleted` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_pop_pollid` (`pollid`)
) ENGINE=InnoDB AUTO_INCREMENT=133 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_poll_question
CREATE TABLE IF NOT EXISTS `SS13_poll_question` (
  `id` int NOT NULL AUTO_INCREMENT,
  `polltype` enum('OPTION','TEXT','NUMVAL','MULTICHOICE','IRV') NOT NULL,
  `created_datetime` datetime NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `question` varchar(255) NOT NULL,
  `subtitle` varchar(255) DEFAULT NULL,
  `adminonly` tinyint unsigned NOT NULL,
  `multiplechoiceoptions` int DEFAULT NULL,
  `createdby_ckey` varchar(32) NOT NULL,
  `createdby_ip` int unsigned NOT NULL,
  `dontshow` tinyint unsigned NOT NULL,
  `minimumplaytime` int NOT NULL,
  `allow_revoting` tinyint unsigned NOT NULL,
  `deleted` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_pquest_question_time_ckey` (`question`,`starttime`,`endtime`,`createdby_ckey`,`createdby_ip`),
  KEY `idx_pquest_time_deleted_id` (`starttime`,`endtime`,`deleted`,`id`),
  KEY `idx_pquest_id_time_type_admin` (`id`,`starttime`,`endtime`,`polltype`,`adminonly`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_poll_textreply
CREATE TABLE IF NOT EXISTS `SS13_poll_textreply` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `pollid` int NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `ip` int unsigned NOT NULL,
  `replytext` varchar(2048) NOT NULL,
  `adminrank` varchar(32) NOT NULL,
  `deleted` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_ptext_pollid_ckey` (`pollid`,`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=220 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_poll_vote
CREATE TABLE IF NOT EXISTS `SS13_poll_vote` (
  `id` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `pollid` int NOT NULL,
  `optionid` int NOT NULL,
  `ckey` varchar(32) NOT NULL,
  `ip` int unsigned NOT NULL,
  `adminrank` varchar(32) NOT NULL,
  `rating` int DEFAULT NULL,
  `deleted` tinyint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_pvote_pollid_ckey` (`pollid`,`ckey`),
  KEY `idx_pvote_optionid_ckey` (`optionid`,`ckey`)
) ENGINE=InnoDB AUTO_INCREMENT=3936 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_preferences
CREATE TABLE IF NOT EXISTS `SS13_preferences` (
  `ckey` varchar(32) NOT NULL,
  `asaycolor` varchar(7) DEFAULT NULL,
  `ooccolor` varchar(7) DEFAULT NULL,
  `lastchangelog` varchar(50) DEFAULT NULL,
  `ui_style` varchar(50) DEFAULT NULL,
  `hotkeys` tinyint unsigned DEFAULT NULL,
  `tgui_fancy` tinyint unsigned DEFAULT NULL,
  `tgui_lock` tinyint unsigned DEFAULT NULL,
  `buttons_locked` tinyint unsigned DEFAULT NULL,
  `windowflashing` tinyint unsigned DEFAULT NULL,
  `default_slot` tinyint unsigned DEFAULT NULL,
  `toggles` smallint unsigned DEFAULT NULL,
  `chat_toggles` smallint unsigned DEFAULT NULL,
  `clientfps` smallint unsigned DEFAULT NULL,
  `parallax` tinyint DEFAULT NULL,
  `ambientocclusion` tinyint unsigned DEFAULT NULL,
  `auto_fit_viewport` tinyint unsigned DEFAULT NULL,
  `ghost_form` varchar(50) DEFAULT NULL,
  `ghost_orbit` varchar(50) DEFAULT NULL,
  `ghost_accs` tinyint unsigned DEFAULT NULL,
  `ghost_others` tinyint unsigned DEFAULT NULL,
  `menuoptions` json DEFAULT NULL,
  `be_special` json DEFAULT NULL,
  `crew_objectives` tinyint unsigned DEFAULT NULL,
  `pda_style` varchar(50) DEFAULT NULL,
  `pda_color` varchar(7) DEFAULT NULL,
  `key_bindings` json DEFAULT NULL,
  `preferred_map` varchar(50) DEFAULT NULL,
  `ghost_hud` tinyint DEFAULT NULL,
  `ignoring` json DEFAULT NULL,
  `inquisitive_ghost` tinyint unsigned DEFAULT NULL,
  `uses_glasses_colour` tinyint unsigned DEFAULT NULL,
  `enable_tips` tinyint unsigned DEFAULT NULL,
  `tip_delay` mediumint unsigned DEFAULT NULL,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_role_time
CREATE TABLE IF NOT EXISTS `SS13_role_time` (
  `ckey` varchar(32) NOT NULL,
  `job` varchar(32) NOT NULL,
  `minutes` int unsigned NOT NULL,
  PRIMARY KEY (`ckey`,`job`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_round
CREATE TABLE IF NOT EXISTS `SS13_round` (
  `id` int NOT NULL AUTO_INCREMENT,
  `initialize_datetime` datetime NOT NULL,
  `start_datetime` datetime DEFAULT NULL,
  `shutdown_datetime` datetime DEFAULT NULL,
  `end_datetime` datetime DEFAULT NULL,
  `server_name` varchar(32) DEFAULT NULL,
  `server_ip` int unsigned NOT NULL,
  `server_port` smallint unsigned NOT NULL,
  `commit_hash` char(40) DEFAULT NULL,
  `game_mode` varchar(32) DEFAULT NULL,
  `game_mode_result` varchar(64) DEFAULT NULL,
  `end_state` varchar(64) DEFAULT NULL,
  `shuttle_name` varchar(64) DEFAULT NULL,
  `map_name` varchar(32) DEFAULT NULL,
  `station_name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8234 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_schema_revision
CREATE TABLE IF NOT EXISTS `SS13_schema_revision` (
  `major` tinyint unsigned NOT NULL,
  `minor` tinyint unsigned NOT NULL,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`major`,`minor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_stickyban
CREATE TABLE IF NOT EXISTS `SS13_stickyban` (
  `ckey` varchar(32) NOT NULL,
  `reason` varchar(2048) NOT NULL,
  `banning_admin` varchar(32) NOT NULL,
  `datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_stickyban_matched_cid
CREATE TABLE IF NOT EXISTS `SS13_stickyban_matched_cid` (
  `stickyban` varchar(32) NOT NULL,
  `matched_cid` varchar(32) NOT NULL,
  `first_matched` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_matched` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`stickyban`,`matched_cid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_stickyban_matched_ckey
CREATE TABLE IF NOT EXISTS `SS13_stickyban_matched_ckey` (
  `stickyban` varchar(32) NOT NULL,
  `matched_ckey` varchar(32) NOT NULL,
  `first_matched` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_matched` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `exempt` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`stickyban`,`matched_ckey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица freerp.SS13_stickyban_matched_ip
CREATE TABLE IF NOT EXISTS `SS13_stickyban_matched_ip` (
  `stickyban` varchar(32) NOT NULL,
  `matched_ip` int unsigned NOT NULL,
  `first_matched` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_matched` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`stickyban`,`matched_ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
